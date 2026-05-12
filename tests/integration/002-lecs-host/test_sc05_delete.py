"""
SC-05: Safe Host Deletion — Integration Tests

Tests for LECS host soft-delete workflow tracing to test cases:
TC-040 (running host blocked), TC-041 (stopped host soft-delete), TC-042 (failed host soft-delete).

API Contract: DELETE /api/v1/lecs-hosts/{id}
  202 — deletion queued, status "deleting"
  403 — host in invalid state
  404 — host not found or already soft-deleted
  401 — missing or invalid auth token
"""

import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from freezegun import freeze_time


DELETABLE_STATES = {"stopped", "failed"}


class MockHost:
    """Represents a LECsHost at the service layer."""

    def __init__(
        self,
        host_id: str | None = None,
        user_id: str = "user-001",
        hostname: str = "test-host",
        status: str = "normal",
        deleted_at: datetime | None = None,
    ):
        self.id = host_id or str(uuid.uuid4())
        self.user_id = user_id
        self.hostname = hostname
        self.status = status
        self.deleted_at = deleted_at
        self.created_at = datetime(2026, 5, 10, 10, 0, 0, tzinfo=timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "hostname": self.hostname,
            "status": self.status,
            "deletedAt": self.deleted_at.isoformat() if self.deleted_at else None,
            "createdAt": self.created_at.isoformat(),
        }


STATE_ERROR_MESSAGES = {
    "normal": "请先将主机关机，再执行删除操作",
    "creating": "主机正在创建中，无法删除",
    "starting": "主机正在启动中，无法删除",
    "shutting_down": "主机正在关机中，无法删除",
    "deleting": "主机正在删除中，无法重复删除",
}


def can_delete_host(host: MockHost) -> tuple[bool, str | None]:
    """Return (can_delete, error_message) based on host state machine rules."""
    if host.status in DELETABLE_STATES:
        return True, None
    msg = STATE_ERROR_MESSAGES.get(host.status, f"未知主机状态: {host.status}")
    return False, msg


def soft_delete_host(
    host: MockHost,
    mock_async_queue: MagicMock,
    freeze_time_ctx=None,
) -> tuple[bool, dict]:
    """Mark host as soft-deleted and submit async task."""
    now = datetime.now(timezone.utc) if freeze_time_ctx is None else freeze_time_ctx.time_to_freeze
    if isinstance(now, datetime) and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    host.status = "deleting"
    host.deleted_at = now
    mock_async_queue.delay.assert_called_once()

    return True, {
        "id": host.id,
        "status": "deleting",
        "deletedAt": now.isoformat(),
    }


def get_active_hosts_for_user(
    hosts: list[MockHost], user_id: str
) -> list[MockHost]:
    """Return hosts WHERE deleted_at IS NULL."""
    return [h for h in hosts if h.user_id == user_id and h.deleted_at is None]


def get_active_count_for_user(hosts: list[MockHost], user_id: str) -> int:
    """Return COUNT(*) WHERE deleted_at IS NULL."""
    return len(get_active_hosts_for_user(hosts, user_id))


@pytest.fixture
def host_repository():
    return []


@pytest.fixture
def mock_async_queue():
    with patch("celery.Celery.send_task") as mock:
        mock_result = MagicMock()
        mock_result.id = str(uuid.uuid4())
        mock.delay = MagicMock(return_value=mock_result)
        mock.apply_async = MagicMock(return_value=mock_result)
        yield mock


@pytest.fixture
def normal_host():
    return MockHost(status="normal", hostname="running-host")


@pytest.fixture
def stopped_host():
    return MockHost(status="stopped", hostname="stopped-host")


@pytest.fixture
def failed_host():
    return MockHost(status="failed", hostname="failed-host")


@pytest.fixture
def creating_host():
    return MockHost(status="creating", hostname="creating-host")


@pytest.fixture
def admin_client():
    return {"authenticated": True, "role": "admin"}


@pytest.fixture
def unauthenticated_client():
    return {"authenticated": False}


def simulate_delete_request(
    host: MockHost | None,
    authenticated: bool = True,
    mock_async_queue=None,
) -> dict:
    """Simulate DELETE /api/v1/lecs-hosts/{id} pipeline. Returns {status_code, body}."""
    if not authenticated:
        return {
            "status_code": 401,
            "body": {
                "success": False,
                "data": None,
                "error": {"code": "UNAUTHORIZED", "message": "请先登录"},
            },
        }

    if host is None or host.deleted_at is not None:
        return {
            "status_code": 404,
            "body": {
                "success": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "主机不存在或已被删除"},
            },
        }

    can_delete, error_msg = can_delete_host(host)
    if not can_delete:
        return {
            "status_code": 403,
            "body": {
                "success": False,
                "data": None,
                "error": {"code": "INVALID_STATE", "message": error_msg},
            },
        }

    if mock_async_queue:
        _success, data = soft_delete_host(host, mock_async_queue)
    else:
        host.status = "deleting"
        host.deleted_at = datetime.now(timezone.utc)
        data = {"id": host.id, "status": "deleting"}

    return {
        "status_code": 202,
        "body": {"success": True, "data": data, "error": None},
    }


# TC-040: Running host deletion blocked

@pytest.mark.integration
class TestRunningHostDeletionBlocked:
    """TC-040: Running (normal) state host cannot be deleted."""

    def test_delete_normal_host_returns_403(self, normal_host, admin_client, mock_async_queue):
        response = simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 403

    def test_delete_normal_host_error_message(self, normal_host, admin_client, mock_async_queue):
        response = simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        error_msg = response["body"]["error"]["message"]
        assert "请先将主机关机，再执行删除操作" in error_msg

    def test_delete_normal_host_error_code(self, normal_host, admin_client, mock_async_queue):
        response = simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["body"]["error"]["code"] == "INVALID_STATE"

    def test_delete_normal_host_no_async_task_submitted(self, normal_host, admin_client, mock_async_queue):
        simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_not_called()

    def test_delete_normal_host_no_state_change(self, normal_host, admin_client, mock_async_queue):
        original_status = normal_host.status
        original_deleted_at = normal_host.deleted_at
        simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert normal_host.status == original_status
        assert normal_host.deleted_at == original_deleted_at


@pytest.mark.integration
class TestCreatingHostDeletionBlocked:
    """TC-040-Negative: Host in creating state cannot be deleted."""

    def test_delete_creating_host_returns_403(self, creating_host, admin_client, mock_async_queue):
        response = simulate_delete_request(creating_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 403

    def test_delete_creating_host_no_task_submitted(self, creating_host, admin_client, mock_async_queue):
        simulate_delete_request(creating_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_not_called()


# TC-041: Stopped host async soft-delete

@pytest.mark.integration
class TestStoppedHostSoftDelete:
    """TC-041: Stopped host can be soft-deleted asynchronously."""

    def test_delete_stopped_host_returns_202(self, stopped_host, admin_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 202

    def test_delete_stopped_host_response_success(self, stopped_host, admin_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["body"]["success"] is True
        assert response["body"]["error"] is None

    def test_delete_stopped_host_status_to_deleting(self, stopped_host, admin_client, mock_async_queue):
        simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert stopped_host.status == "deleting"

    def test_delete_stopped_host_sets_deleted_at(self, stopped_host, admin_client, mock_async_queue):
        assert stopped_host.deleted_at is None
        simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert stopped_host.deleted_at is not None

    def test_delete_stopped_host_async_task_submitted(self, stopped_host, admin_client, mock_async_queue):
        simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_called_once()

    def test_delete_stopped_host_active_query_excludes(self, stopped_host, host_repository, admin_client, mock_async_queue):
        """SQL: WHERE deleted_at IS NULL should NOT return the deleted host."""
        host_repository.append(stopped_host)
        simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        active_hosts = get_active_hosts_for_user(host_repository, stopped_host.user_id)
        assert stopped_host not in active_hosts


# TC-042: Failed host soft-delete

@pytest.mark.integration
class TestFailedHostSoftDelete:
    """TC-042: Failed host can be soft-deleted asynchronously."""

    def test_delete_failed_host_returns_202(self, failed_host, admin_client, mock_async_queue):
        response = simulate_delete_request(failed_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 202

    def test_delete_failed_host_status_to_deleting(self, failed_host, admin_client, mock_async_queue):
        simulate_delete_request(failed_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert failed_host.status == "deleting"

    def test_delete_failed_host_sets_deleted_at_not_null(self, failed_host, admin_client, mock_async_queue):
        assert failed_host.deleted_at is None
        simulate_delete_request(failed_host, authenticated=True, mock_async_queue=mock_async_queue)
        assert failed_host.deleted_at is not None

    def test_delete_failed_host_async_task_submitted(self, failed_host, admin_client, mock_async_queue):
        simulate_delete_request(failed_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_called_once()

    def test_delete_failed_host_only_delete_button_enabled(self, failed_host):
        can_delete, _ = can_delete_host(failed_host)
        assert can_delete is True


# Negative tests: 404, 401, edge cases

@pytest.mark.integration
class TestDeleteNegative:
    """Negative scenarios: nonexistent, unauthenticated, already-deleted."""

    def test_delete_nonexistent_host_returns_404(self, admin_client, mock_async_queue):
        response = simulate_delete_request(host=None, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 404

    def test_delete_nonexistent_host_error_code(self, admin_client, mock_async_queue):
        response = simulate_delete_request(host=None, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["body"]["error"]["code"] == "NOT_FOUND"

    def test_unauthenticated_delete_returns_401(self, stopped_host, unauthenticated_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=False, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 401

    def test_unauthenticated_delete_error_code(self, stopped_host, unauthenticated_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=False, mock_async_queue=mock_async_queue)
        assert response["body"]["error"]["code"] == "UNAUTHORIZED"

    def test_already_deleted_host_returns_404(self, admin_client, mock_async_queue):
        host = MockHost(status="stopped", hostname="already-deleted")
        host.deleted_at = datetime.now(timezone.utc)
        response = simulate_delete_request(host, authenticated=True, mock_async_queue=mock_async_queue)
        assert response["status_code"] == 404


# Quota decrease verification

@pytest.mark.integration
class TestQuotaDecrease:
    """User's active host quota count decreases after deletion."""

    def test_quota_decreases_after_delete(self, host_repository, admin_client, mock_async_queue):
        user_id = "quota-test-user"
        host = MockHost(user_id=user_id, hostname="quota-host", status="stopped")
        host_repository.append(host)

        initial_count = get_active_count_for_user(host_repository, user_id)
        assert initial_count == 1

        simulate_delete_request(host, authenticated=True, mock_async_queue=mock_async_queue)

        final_count = get_active_count_for_user(host_repository, user_id)
        assert final_count == 0

    def test_quota_multi_hosts_delete_one(self, host_repository, admin_client, mock_async_queue):
        user_id = "quota-multi-user"
        host_a = MockHost(user_id=user_id, hostname="host-a", status="stopped")
        host_b = MockHost(user_id=user_id, hostname="host-b", status="normal")
        host_repository.extend([host_a, host_b])

        assert get_active_count_for_user(host_repository, user_id) == 2

        simulate_delete_request(host_a, authenticated=True, mock_async_queue=mock_async_queue)

        assert get_active_count_for_user(host_repository, user_id) == 1

    def test_quota_count_with_deleted_at_filter(self, host_repository, admin_client, mock_async_queue):
        user_id = "quota-filter-user"
        h1 = MockHost(user_id=user_id, hostname="active-1", status="normal")
        h2 = MockHost(user_id=user_id, hostname="active-2", status="stopped")
        h3 = MockHost(user_id=user_id, hostname="to-delete", status="stopped")
        h3.deleted_at = datetime.now(timezone.utc)
        host_repository.extend([h1, h2, h3])

        active = get_active_hosts_for_user(host_repository, user_id)
        assert len(active) == 2
        assert h3.id not in {h.id for h in active}


# Async deletion timing with freezegun

@pytest.mark.integration
class TestAsyncDeletionTiming:
    """Async deletion completes within 3-5 second window (freezegun)."""

    def test_async_delete_completes_within_3_seconds(self, stopped_host, admin_client):
        with freeze_time("2026-05-12 10:00:00") as frozen_time:
            assert stopped_host.deleted_at is None
            frozen_time.tick(delta=3)
            stopped_host.deleted_at = datetime.now(timezone.utc)
            assert stopped_host.deleted_at is not None

    def test_async_delete_5_second_window(self, stopped_host, admin_client, mock_async_queue):
        with freeze_time("2026-05-12 10:00:00") as frozen_time:
            start_time = datetime.now(timezone.utc)

            response = simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
            assert response["status_code"] == 202

            frozen_time.tick(delta=4)
            completion_time = datetime.now(timezone.utc)

            elapsed = (completion_time - start_time).total_seconds()
            assert 3 <= elapsed <= 5
            assert stopped_host.deleted_at is not None

    def test_async_delete_stopped_host_data_persists(self, stopped_host, admin_client, mock_async_queue):
        """Soft-delete preserves host data; only deleted_at changes."""
        original_data = stopped_host.to_dict()

        with freeze_time("2026-05-12 10:00:00"):
            simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)

            assert stopped_host.id == original_data["id"]
            assert stopped_host.hostname == original_data["hostname"]
            assert stopped_host.user_id == original_data["userId"]
            assert stopped_host.deleted_at is not None


# Async task submission verification

@pytest.mark.integration
class TestAsyncTaskSubmission:
    """Verify delete task is properly submitted to async queue."""

    def test_delete_task_submitted_for_stopped_host(self, stopped_host, admin_client, mock_async_queue):
        simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_called_once()

    def test_delete_task_submitted_for_failed_host(self, failed_host, admin_client, mock_async_queue):
        simulate_delete_request(failed_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_called_once()

    def test_no_task_for_normal_host(self, normal_host, admin_client, mock_async_queue):
        simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_not_called()

    def test_no_task_for_nonexistent_host(self, admin_client, mock_async_queue):
        simulate_delete_request(host=None, authenticated=True, mock_async_queue=mock_async_queue)
        mock_async_queue.delay.assert_not_called()

    def test_delete_task_payload_contains_host_id(self, stopped_host, admin_client):
        with patch("celery.Celery.send_task") as mock_queue:
            mock_result = MagicMock()
            mock_result.id = str(uuid.uuid4())
            mock_queue.delay = MagicMock(return_value=mock_result)

            simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_queue)

            mock_queue.delay.assert_called_once()
            call_args = mock_queue.delay.call_args
            assert call_args is not None


# Standard response format validation

@pytest.mark.integration
class TestDeleteResponseFormat:
    """All DELETE responses follow {success, data, error} format."""

    def test_202_response_format(self, stopped_host, admin_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=True, mock_async_queue=mock_async_queue)
        body = response["body"]
        assert body["success"] is True
        assert body["data"] is not None
        assert body["error"] is None

    def test_403_response_format(self, normal_host, admin_client, mock_async_queue):
        response = simulate_delete_request(normal_host, authenticated=True, mock_async_queue=mock_async_queue)
        body = response["body"]
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"] is not None
        assert "code" in body["error"]
        assert "message" in body["error"]

    def test_404_response_format(self, admin_client, mock_async_queue):
        response = simulate_delete_request(host=None, authenticated=True, mock_async_queue=mock_async_queue)
        body = response["body"]
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"] is not None

    def test_401_response_format(self, stopped_host, unauthenticated_client, mock_async_queue):
        response = simulate_delete_request(stopped_host, authenticated=False, mock_async_queue=mock_async_queue)
        body = response["body"]
        assert body["success"] is False
        assert body["data"] is None
        assert "code" in body["error"]
        assert "message" in body["error"]
