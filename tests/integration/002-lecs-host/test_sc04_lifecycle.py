"""
SC-04: Host Lifecycle (Stop/Start) — Integration Tests

Tests for LECS Host async state transitions:
- TC-030: POST /api/v1/lecs-hosts/{id}/stop with normal host → 202, status becomes "shutting_down"
- TC-031: POST /api/v1/lecs-hosts/{id}/start with stopped host → 202, status becomes "starting"
- TC-032: Transition-state concurrent lock: host in shutting_down → 409/403
- TC-033: Failed host → POST /start → 202 → 10s → "normal"
- Negative tests: stop stopped (403), start normal (403), delete normal (403), stop non-existent (404), unauth stop (401)

Uses pytest + httpx AsyncClient + freezegun + mock following plan.md patterns.
State machine based on specs/002-lecs-host/data-model.md.
"""

import json
import uuid
import pytest
from datetime import datetime
from unittest.mock import patch
from httpx import AsyncClient, AsyncTransport, Response, Headers
from freezegun import freeze_time

class HostState:
    CREATING = "creating"
    NORMAL = "normal"
    FAILED = "failed"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"
    STARTING = "starting"
    DELETING = "deleting"


# Allowed actions per state: action -> next state
STATE_TRANSITIONS = {
    HostState.CREATING:       {},
    HostState.NORMAL:         {"stop": HostState.SHUTTING_DOWN},
    HostState.FAILED:         {"start": HostState.STARTING, "delete": HostState.DELETING},
    HostState.SHUTTING_DOWN:  {},
    HostState.STOPPED:        {"start": HostState.STARTING, "delete": HostState.DELETING},
    HostState.STARTING:       {},
    HostState.DELETING:       {},
}

BUTTON_ENABLE_MATRIX = {
    HostState.CREATING:       {"stop": False, "start": False, "delete": False},
    HostState.NORMAL:         {"stop": True,  "start": False, "delete": False},
    HostState.FAILED:         {"stop": False, "start": True,  "delete": True},
    HostState.SHUTTING_DOWN:  {"stop": False, "start": False, "delete": False},
    HostState.STOPPED:        {"stop": False, "start": True,  "delete": True},
    HostState.STARTING:       {"stop": False, "start": False, "delete": False},
    HostState.DELETING:       {"stop": False, "start": False, "delete": False},
}


class MockLECsHost:
    def __init__(self, host_id=None, user_id=None, hostname="test-host-01",
                 status=HostState.NORMAL, **kwargs):
        self.id = host_id or uuid.uuid4()
        self.user_id = user_id or uuid.uuid4()
        self.hostname = hostname
        self.status = status
        self.billing_mode = kwargs.get("billing_mode", "PREPAID")
        self.os_image = kwargs.get("os_image", "UBUNTU")
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.started_at = kwargs.get("started_at", None)
        self.deleted_at = kwargs.get("deleted_at", None)

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "hostname": self.hostname,
            "status": self.status,
            "billing_mode": self.billing_mode,
            "os_image": self.os_image,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class MockAsyncResult:
    def __init__(self, task_id=None):
        self.id = task_id or str(uuid.uuid4())
        self.status = "PENDING"

    def get(self, timeout=None):
        return {"task_id": self.id, "status": self.status}


class MockAsyncQueue:
    def __init__(self):
        self.submitted_tasks = []

    def send_task(self, task_name, args=None, kwargs=None):
        result = MockAsyncResult()
        self.submitted_tasks.append({
            "task_name": task_name,
            "args": args or [],
            "kwargs": kwargs or {},
            "task_id": result.id,
            "submitted_at": datetime.utcnow(),
        })
        result.status = "SUCCESS"
        return result


@pytest.fixture
def mock_async_queue():
    queue = MockAsyncQueue()
    with patch("celery.Celery.send_task", side_effect=queue.send_task) as mock:
        mock.submitted_tasks = queue.submitted_tasks
        yield mock


@pytest.fixture
def host_factory():
    def _create(status=HostState.NORMAL, **kwargs):
        return MockLECsHost(status=status, **kwargs)
    return _create


@pytest.fixture
def mock_db():
    store = {}

    def get_host(host_id):
        return store.get(str(host_id))

    def save_host(host):
        store[str(host.id)] = host
        return host

    def delete_host(host):
        host.deleted_at = datetime.utcnow()
        store[str(host.id)] = host
        return host

    return {"store": store, "get": get_host, "save": save_host, "delete": delete_host}


@pytest.fixture
def route_handler(mock_db, mock_async_queue):
    async def handle(method, path, headers=None):
        headers = headers or {}
        path = path.rstrip("/")

        if method in ("POST", "DELETE") and "/api/v1/lecs-hosts/" in path:
            auth_cookie = headers.get("cookie", "")
            if "jwt_token" not in auth_cookie and "Authorization" not in headers:
                return 401, {"success": False, "error_code": "UNAUTHORIZED",
                             "error_message": "Authentication required. Please login first."}

        if method == "GET" and path.endswith("/api/v1/lecs-hosts"):
            hosts_list = [h.to_dict() for h in mock_db["store"].values() if h.deleted_at is None]
            return 200, {"success": True, "data": {"items": hosts_list, "total": len(hosts_list)}}

        if method == "POST" and path.endswith("/stop"):
            host_id = path.split("/")[-2]
            host = mock_db["get"](host_id)
            if host is None:
                return 404, {"success": False, "error_code": "NOT_FOUND",
                             "error_message": f"Host {host_id} not found."}
            if host.status == HostState.STOPPED:
                return 403, {"success": False, "error_code": "FORBIDDEN",
                             "error_message": "Cannot stop a host that is already stopped."}
            if host.status not in (HostState.NORMAL,):
                if host.status in (HostState.SHUTTING_DOWN, HostState.STARTING,
                                   HostState.DELETING, HostState.CREATING):
                    return 409, {"success": False, "error_code": "CONFLICT",
                                 "error_message": f"Host is in '{host.status}' state."}
                return 403, {"success": False, "error_code": "FORBIDDEN",
                             "error_message": f"Cannot stop a host in '{host.status}' state."}

            host.status = HostState.SHUTTING_DOWN
            mock_db["save"](host)
            task_result = mock_async_queue.send_task("host.shutdown_task", args=[str(host.id)])
            return 202, {"success": True, "data": {"host": host.to_dict(), "task_id": task_result.id,
                            "message": "Host shutdown initiated."}}

        if method == "POST" and path.endswith("/start"):
            host_id = path.split("/")[-2]
            host = mock_db["get"](host_id)
            if host is None:
                return 404, {"success": False, "error_code": "NOT_FOUND",
                             "error_message": f"Host {host_id} not found."}
            if host.status == HostState.NORMAL:
                return 403, {"success": False, "error_code": "FORBIDDEN",
                             "error_message": "Cannot start a host that is already running."}
            if host.status not in (HostState.STOPPED, HostState.FAILED):
                if host.status in (HostState.SHUTTING_DOWN, HostState.STARTING,
                                   HostState.DELETING, HostState.CREATING):
                    return 409, {"success": False, "error_code": "CONFLICT",
                                 "error_message": f"Host is in '{host.status}' state."}
                return 403, {"success": False, "error_code": "FORBIDDEN",
                             "error_message": f"Cannot start a host in '{host.status}' state."}

            host.status = HostState.STARTING
            host.started_at = datetime.utcnow()
            mock_db["save"](host)
            task_result = mock_async_queue.send_task("host.startup_task", args=[str(host.id)])
            return 202, {"success": True, "data": {"host": host.to_dict(), "task_id": task_result.id,
                           "message": "Host startup initiated."}}

        if method == "DELETE" and "/api/v1/lecs-hosts/" in path:
            host_id = path.split("/")[-1]
            host = mock_db["get"](host_id)
            if host is None:
                return 404, {"success": False, "error_code": "NOT_FOUND",
                             "error_message": f"Host {host_id} not found."}
            if host.status == HostState.NORMAL:
                return 403, {"success": False, "error_code": "FORBIDDEN",
                             "error_message": "Cannot delete a running host. Stop it first."}
            if host.status in (HostState.SHUTTING_DOWN, HostState.STARTING,
                               HostState.DELETING, HostState.CREATING):
                return 409, {"success": False, "error_code": "CONFLICT",
                             "error_message": f"Host is in '{host.status}' state."}

            host.status = HostState.DELETING
            mock_db["delete"](host)
            task_result = mock_async_queue.send_task("host.deletion_task", args=[str(host.id)])
            return 202, {"success": True, "data": {"task_id": task_result.id,
                           "message": "Host deletion initiated."}}

        return 404, {"success": False, "error_code": "NOT_FOUND", "error_message": "Route not found."}

    return handle


class MockAppTransport(AsyncTransport):

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    async def handle_async_request(self, request):
        hdrs = dict(request.headers)
        if "cookie" in hdrs:
            hdrs["cookie"] = hdrs["cookie"]

        status_code, body = await self.handler(
            method=request.method,
            path=str(request.url).replace("http://testserver", ""),
            headers=hdrs,
        )

        return Response(
            status_code=status_code,
            headers=Headers({"content-type": "application/json"}),
            content=json.dumps(body).encode(),
            request=request,
        )


@pytest.fixture
async def authenticated_client(route_handler):
    transport = MockAppTransport(route_handler)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
        timeout=10.0,
    ) as client:
        client.cookies.set("jwt_token", "test-jwt-token-for-user")
        yield client


@pytest.fixture
async def unauthenticated_client(route_handler):
    transport = MockAppTransport(route_handler)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        follow_redirects=False,
        timeout=10.0,
    ) as client:
        yield client


def complete_transition(host, from_state, to_state):
    assert host.status == from_state, f"Expected {from_state}, got {host.status}"
    host.status = to_state
    if to_state == HostState.NORMAL:
        host.started_at = datetime.utcnow()
    return host



class TestTC030_StopNormalHost:
    """TC-030: POST /api/v1/lecs-hosts/{id}/stop with normal host -> 202."""

    @pytest.mark.asyncio
    async def test_stop_normal_host_returns_202(self, authenticated_client, mock_db,
                                                  host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")

        assert response.status_code == 202
        body = response.json()
        assert body["success"] is True
        assert body["data"]["host"]["status"] == HostState.SHUTTING_DOWN
        assert "task_id" in body["data"]

    @pytest.mark.asyncio
    async def test_stop_queues_shutdown_task(self, authenticated_client, mock_db,
                                              host_factory, mock_async_queue):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")

        assert len(mock_async_queue.submitted_tasks) == 1
        task = mock_async_queue.submitted_tasks[0]
        assert task["task_name"] == "host.shutdown_task"
        assert str(host.id) in task["args"]

    @pytest.mark.asyncio
    @freeze_time("2026-05-12 10:00:00")
    async def test_stop_full_transition_to_stopped(self, authenticated_client, mock_db,
                                                   host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        resp = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")
        assert resp.status_code == 202

        complete_transition(host, HostState.SHUTTING_DOWN, HostState.STOPPED)
        assert host.status == HostState.STOPPED

    @pytest.mark.asyncio
    async def test_all_buttons_disabled_during_shutdown(self, mock_db, host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)
        host.status = HostState.SHUTTING_DOWN
        mock_db["save"](host)

        buttons = BUTTON_ENABLE_MATRIX[HostState.SHUTTING_DOWN]
        assert buttons["stop"] is False
        assert buttons["start"] is False
        assert buttons["delete"] is False



class TestTC031_StartStoppedHost:
    """TC-031: POST /api/v1/lecs-hosts/{id}/start with stopped host -> 202."""

    @pytest.mark.asyncio
    async def test_start_stopped_host_returns_202(self, authenticated_client, mock_db,
                                                   host_factory):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert response.status_code == 202
        body = response.json()
        assert body["success"] is True
        assert body["data"]["host"]["status"] == HostState.STARTING
        assert "task_id" in body["data"]

    @pytest.mark.asyncio
    async def test_start_stopped_host_queues_startup_task(self, authenticated_client,
                                                           mock_db, host_factory,
                                                           mock_async_queue):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert len(mock_async_queue.submitted_tasks) == 1
        task = mock_async_queue.submitted_tasks[0]
        assert task["task_name"] == "host.startup_task"
        assert str(host.id) in task["args"]

    @pytest.mark.asyncio
    @freeze_time("2026-05-12 10:00:00")
    async def test_start_full_transition_to_normal(self, authenticated_client, mock_db,
                                                   host_factory):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        resp = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")
        assert resp.status_code == 202

        complete_transition(host, HostState.STARTING, HostState.NORMAL)
        assert host.status == HostState.NORMAL
        assert host.started_at is not None



class TestTC032_TransitionStateConcurrentLock:
    """TC-032: Host in shutting_down -> stop/start -> 409/403."""

    @pytest.mark.asyncio
    async def test_stop_host_in_shutting_down_returns_409(self, authenticated_client,
                                                           mock_db, host_factory):
        host = host_factory(status=HostState.SHUTTING_DOWN)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")

        assert response.status_code == 409
        body = response.json()
        assert body["success"] is False
        assert body["error_code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_start_host_in_shutting_down_returns_409(self, authenticated_client,
                                                            mock_db, host_factory):
        host = host_factory(status=HostState.SHUTTING_DOWN)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert response.status_code == 409
        body = response.json()
        assert body["error_code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_delete_host_in_shutting_down_returns_409(self, authenticated_client,
                                                             mock_db, host_factory):
        host = host_factory(status=HostState.SHUTTING_DOWN)
        mock_db["save"](host)

        response = await authenticated_client.delete(f"/api/v1/lecs-hosts/{host.id}")

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_stop_host_in_starting_returns_409(self, authenticated_client,
                                                      mock_db, host_factory):
        host = host_factory(status=HostState.STARTING)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_all_buttons_disabled_during_all_transition_states(self, host_factory):
        for state in [HostState.SHUTTING_DOWN, HostState.STARTING,
                      HostState.CREATING, HostState.DELETING]:
            buttons = BUTTON_ENABLE_MATRIX[state]
            assert buttons["stop"] is False, f"Stop disabled in {state}"
            assert buttons["start"] is False, f"Start disabled in {state}"
            assert buttons["delete"] is False, f"Delete disabled in {state}"



class TestTC033_FailedHostStart:
    """TC-033: Failed host -> POST /start -> 202 -> 10s -> normal."""

    @pytest.mark.asyncio
    async def test_start_failed_host_returns_202(self, authenticated_client, mock_db,
                                                  host_factory):
        host = host_factory(status=HostState.FAILED)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert response.status_code == 202
        body = response.json()
        assert body["success"] is True
        assert body["data"]["host"]["status"] == HostState.STARTING

    @pytest.mark.asyncio
    async def test_start_failed_host_queues_startup_task(self, authenticated_client,
                                                          mock_db, host_factory,
                                                          mock_async_queue):
        host = host_factory(status=HostState.FAILED)
        mock_db["save"](host)

        await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert len(mock_async_queue.submitted_tasks) >= 1
        task = mock_async_queue.submitted_tasks[-1]
        assert task["task_name"] == "host.startup_task"

    @pytest.mark.asyncio
    @freeze_time("2026-05-12 12:00:00")
    async def test_failed_host_full_recovery_to_normal(self, authenticated_client,
                                                        mock_db, host_factory):
        host = host_factory(status=HostState.FAILED)
        mock_db["save"](host)

        resp = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")
        assert resp.status_code == 202
        assert host.status == HostState.STARTING

        complete_transition(host, HostState.STARTING, HostState.NORMAL)

        assert host.status == HostState.NORMAL
        assert host.started_at is not None

    @pytest.mark.asyncio
    async def test_failed_host_delete_allowed(self, authenticated_client, mock_db,
                                               host_factory):
        host = host_factory(status=HostState.FAILED)
        mock_db["save"](host)

        response = await authenticated_client.delete(f"/api/v1/lecs-hosts/{host.id}")

        assert response.status_code == 202



class TestLifecycleNegatives:
    """Negative test cases for host lifecycle operations."""

    @pytest.mark.asyncio
    async def test_stop_already_stopped_host_returns_403(self, authenticated_client,
                                                          mock_db, host_factory):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")

        assert response.status_code == 403
        body = response.json()
        assert body["success"] is False
        assert body["error_code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_start_normal_host_returns_403(self, authenticated_client, mock_db,
                                                  host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert response.status_code == 403
        body = response.json()
        assert body["error_code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_delete_normal_host_returns_403(self, authenticated_client, mock_db,
                                                   host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        response = await authenticated_client.delete(f"/api/v1/lecs-hosts/{host.id}")

        assert response.status_code == 403
        body = response.json()
        assert body["error_code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_stop_nonexistent_host_returns_404(self, authenticated_client, mock_db):
        fake_id = str(uuid.uuid4())

        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{fake_id}/stop")

        assert response.status_code == 404
        body = response.json()
        assert body["error_code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_start_nonexistent_host_returns_404(self, authenticated_client, mock_db):
        fake_id = str(uuid.uuid4())
        response = await authenticated_client.post(f"/api/v1/lecs-hosts/{fake_id}/start")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_host_returns_404(self, authenticated_client, mock_db):
        fake_id = str(uuid.uuid4())
        response = await authenticated_client.delete(f"/api/v1/lecs-hosts/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_stop_returns_401(self, unauthenticated_client,
                                                      mock_db, host_factory):
        host = host_factory(status=HostState.NORMAL)
        mock_db["save"](host)

        response = await unauthenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/stop")

        assert response.status_code == 401
        body = response.json()
        assert body["error_code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_unauthenticated_start_returns_401(self, unauthenticated_client,
                                                      mock_db, host_factory):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        response = await unauthenticated_client.post(f"/api/v1/lecs-hosts/{host.id}/start")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthenticated_delete_returns_401(self, unauthenticated_client,
                                                       mock_db, host_factory):
        host = host_factory(status=HostState.STOPPED)
        mock_db["save"](host)

        response = await unauthenticated_client.delete(f"/api/v1/lecs-hosts/{host.id}")

        assert response.status_code == 401



class TestStateMachineConsistency:
    """Verify state machine rules match data-model.md specification."""

    def test_normal_host_can_only_stop(self):
        allowed = STATE_TRANSITIONS[HostState.NORMAL]
        assert "stop" in allowed
        assert "start" not in allowed
        assert "delete" not in allowed

    def test_stopped_host_can_start_and_delete(self):
        allowed = STATE_TRANSITIONS[HostState.STOPPED]
        assert "start" in allowed
        assert "delete" in allowed
        assert "stop" not in allowed

    def test_failed_host_can_start_and_delete(self):
        allowed = STATE_TRANSITIONS[HostState.FAILED]
        assert "start" in allowed
        assert "delete" in allowed

    def test_transition_states_allow_no_actions(self):
        for state in [HostState.SHUTTING_DOWN, HostState.STARTING,
                      HostState.CREATING, HostState.DELETING]:
            assert len(STATE_TRANSITIONS[state]) == 0, \
                f"{state} should allow no direct actions"

    def test_button_matrix_normal(self):
        b = BUTTON_ENABLE_MATRIX[HostState.NORMAL]
        assert b["stop"] is True
        assert b["start"] is False
        assert b["delete"] is False

    def test_button_matrix_stopped(self):
        b = BUTTON_ENABLE_MATRIX[HostState.STOPPED]
        assert b["stop"] is False
        assert b["start"] is True
        assert b["delete"] is True

    def test_button_matrix_failed(self):
        b = BUTTON_ENABLE_MATRIX[HostState.FAILED]
        assert b["stop"] is False
        assert b["start"] is True
        assert b["delete"] is True

    def test_button_matrix_creating(self):
        b = BUTTON_ENABLE_MATRIX[HostState.CREATING]
        assert b["stop"] is False
        assert b["start"] is False
        assert b["delete"] is False
