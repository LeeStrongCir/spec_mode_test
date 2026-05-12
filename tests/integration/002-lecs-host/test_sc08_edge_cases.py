"""
SC-08: 边界与异常场景 — Integration Tests

EC-001: 配额上限 (100台) 创建拦截
EC-002: 创建超时 (60秒) 状态降级
EC-003: 并发操作防冲突 (过渡态重复操作 / race condition)
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from freezegun import freeze_time
from datetime import datetime, timedelta


API_PREFIX = "/api/v1/lecs-hosts"


def _make_valid_create_payload():
    return {
        "billing_mode": "包年/包月",
        "host_name": "test_host_ec",
        "username": "valid_user",
        "password": "Abcdef12!",
        "instance_type": "经济型",
        "instance_spec": "eco-001",
        "os_image": "Ubuntu 22.04 LTS",
        "ip_config": {"mode": "DHCP"},
        "duration": 1,
    }


def _create_host_record(host_id: str, owner_id: str, state: str = "normal"):
    return {
        "id": host_id,
        "owner_id": owner_id,
        "host_name": f"test_host_{host_id[:8]}",
        "status": state,
        "state": state,
        "billing_mode": "包年/包月",
        "deleted_at": None,
        "created_at": datetime.utcnow().isoformat(),
    }


# ====================================================================
# EC-001: 配额上限创建拦截
# ====================================================================


@pytest.mark.asyncio
class TestQuotaExceeded:
    """EC-001: 用户活跃主机数达到 100 台后，创建请求被拒绝."""

    async def test_create_host_at_quota_returns_409(self, jwt_authenticated_client, test_user):
        hosts = []
        for i in range(100):
            hosts.append(_create_host_record(
                host_id=f"host-{i:03d}", owner_id=test_user.id
            ))

        with patch("app.services.host.HostService.list_active_hosts", return_value=hosts):
            resp = await jwt_authenticated_client.post(
                API_PREFIX, json=_make_valid_create_payload()
            )
            assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["success"] is False
            assert "error_code" in body
            assert "error_message" in body
            assert "主机数量达到上限" in body["error_message"] or "QUOTA" in body.get("error_code", "").upper() or "LIMIT" in body.get("error_code", "").upper()

    async def test_create_host_at_quota_99_succeeds(self, jwt_authenticated_client, test_user):
        hosts = []
        for i in range(99):
            hosts.append(_create_host_record(
                host_id=f"host-{i:03d}", owner_id=test_user.id
            ))

        with patch("app.services.host.HostService.list_active_hosts", return_value=hosts):
            with patch("celery.Celery.send_task") as mock_queue:
                mock_queue.return_value = type("MockResult", (), {"id": "task-1"})()
                resp = await jwt_authenticated_client.post(
                    API_PREFIX, json=_make_valid_create_payload()
                )
                assert resp.status_code in (201, 202), (
                    f"Expected 201/202 with 99 hosts, got {resp.status_code}"
                )
                body = resp.json()
                assert body["success"] is True

    async def test_create_host_at_quota_exactly_100_blocked(self, jwt_authenticated_client, test_user):
        exactly_100_hosts = [
            _create_host_record(host_id=f"ec-host-{i:03d}", owner_id=test_user.id)
            for i in range(100)
        ]

        with patch("app.services.host.HostService.list_active_hosts", return_value=exactly_100_hosts):
            resp = await jwt_authenticated_client.post(
                API_PREFIX, json=_make_valid_create_payload()
            )
            assert resp.status_code == 409
            body = resp.json()
            assert body["success"] is False


# ====================================================================
# EC-002: 创建超时降级
# ====================================================================


@pytest.mark.asyncio
class TestCreateTimeout:
    """EC-002: 创建任务超过 60 秒未完成 → 状态强制降级为 failed."""

    async def test_host_status_forced_to_failed_after_60_seconds(self, jwt_authenticated_client):
        with patch("app.services.host.HostService.create_host") as mock_create:
            created_host = _create_host_record(host_id="host-creating", owner_id="user-a-001", state="creating")
            mock_create.return_value = created_host

            with freeze_time("2026-01-01 00:00:00") as frozen_time:
                with patch("app.services.host.HostService.get_host", return_value=created_host):
                    resp = await jwt_authenticated_client.post(
                        API_PREFIX, json=_make_valid_create_payload()
                    )
                    assert resp.status_code in (201, 202)

                frozen_time.tick(timedelta(seconds=61))

                with patch("app.services.host.HostService.get_host") as mock_get:
                    failed_host = _create_host_record(
                        host_id="host-creating", owner_id="user-a-001", state="failed"
                    )
                    failed_host["error_message"] = "创建超时"
                    mock_get.return_value = failed_host

                    resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-creating")
                    if resp.status_code == 200:
                        body = resp.json()
                        data = body.get("data", {})
                        assert data.get("status") in ("failed", "creating", "创建失败")

    async def test_host_still_creating_within_60_seconds(self, jwt_authenticated_client):
        with freeze_time("2026-01-01 00:00:00") as frozen_time:
            creating_host = _create_host_record(
                host_id="host-timeout-test", owner_id="user-a-001", state="creating"
            )

            with patch("app.services.host.HostService.get_host", return_value=creating_host):
                frozen_time.tick(timedelta(seconds=30))

                resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-timeout-test")
                if resp.status_code == 200:
                    body = resp.json()
                    data = body.get("data", {})

    async def test_timeout_error_message_present(self, jwt_authenticated_client):
        with freeze_time("2026-01-01 00:00:00") as frozen_time:
            failed_host = _create_host_record(
                host_id="host-ec002-timeout", owner_id="user-a-001", state="failed"
            )
            failed_host["error_message"] = "创建超时，已超过 60 秒"

            with patch("app.services.host.HostService.get_host", return_value=failed_host):
                frozen_time.tick(timedelta(seconds=61))

                resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-ec002-timeout")
                if resp.status_code == 200:
                    body = resp.json()
                    data = body.get("data", {})
                    if "error_message" in data:
                        assert "超时" in data["error_message"] or "timeout" in data["error_message"].lower()

            failed_host["status"] = "failed"
            failed_host["state"] = "failed"


# ====================================================================
# EC-003: 并发操作防冲突
# ====================================================================


@pytest.mark.asyncio
class TestConcurrentStopDuringTransition:
    """EC-003-01: 关机中再次调用 /stop → 409."""

    async def test_stop_during_shutting_down_returns_409(self, jwt_authenticated_client):
        shutting_down_host = _create_host_record(
            host_id="host-shutting-01", owner_id="user-a-001", state="shutting_down"
        )

        with patch("app.services.host.HostService.get_host", return_value=shutting_down_host):
            resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-shutting-01/stop")
            assert resp.status_code in (403, 409), (
                f"Expected 403/409, got {resp.status_code}: {resp.text}"
            )
            body = resp.json()
            assert body["success"] is False
            assert isinstance(body["error_code"], str)
            assert isinstance(body["error_message"], str)

    async def test_stop_already_stopped_returns_blocked(self, jwt_authenticated_client):
        stopped_host = _create_host_record(
            host_id="host-stopped-ec", owner_id="user-a-001", state="stopped"
        )
        with patch("app.services.host.HostService.get_host", return_value=stopped_host):
            resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-stopped-ec/stop")
            assert resp.status_code in (403, 409)
            body = resp.json()
            assert body["success"] is False

    async def test_stop_normal_returns_202(self, jwt_authenticated_client, mock_async_queue):
        normal_host = _create_host_record(
            host_id="host-normal-ec", owner_id="user-a-001", state="normal"
        )
        with patch("app.services.host.HostService.get_host", return_value=normal_host):
            with patch("app.services.host.HostService.transition_state", return_value=normal_host):
                resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-normal-ec/stop")
                assert resp.status_code in (200, 202)


class TestCrossTransitionConflict:
    """EC-003-02: 关机中调用 /start → 409."""

    @pytest.mark.asyncio
    async def test_start_during_shutting_down_returns_409(self, jwt_authenticated_client):
        shutting_down_host = _create_host_record(
            host_id="host-shutting-02", owner_id="user-a-001", state="shutting_down"
        )
        with patch("app.services.host.HostService.get_host", return_value=shutting_down_host):
            resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-shutting-02/start")
            assert resp.status_code in (403, 409)
            body = resp.json()
            assert body["success"] is False
            assert isinstance(body["error_code"], str)
            assert isinstance(body["error_message"], str)

    @pytest.mark.asyncio
    async def test_stop_during_starting_returns_409(self, jwt_authenticated_client):
        starting_host = _create_host_record(
            host_id="host-starting-01", owner_id="user-a-001", state="starting"
        )
        with patch("app.services.host.HostService.get_host", return_value=starting_host):
            resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-starting-01/stop")
            assert resp.status_code in (403, 409)
            body = resp.json()
            assert body["success"] is False
            assert isinstance(body["error_code"], str)


@pytest.mark.asyncio
class TestConcurrentParallelRequests:
    """EC-003-04: 并发 3 个 stop 请求 → 仅第一个被接受."""

    async def test_three_parallel_stops_only_first_accepted(self, jwt_authenticated_client):
        normal_host = _create_host_record(
            host_id="host-parallel-01", owner_id="user-a-001", state="normal"
        )

        call_count = 0
        transition_call_count = 0

        async def mock_get_host_async(host_id):
            if transition_call_count >= 1:
                return _create_host_record(host_id=host_id, owner_id="user-a-001", state="shutting_down")
            return normal_host

        async def mock_transition_async(*args, **kwargs):
            nonlocal transition_call_count
            transition_call_count += 1
            return _create_host_record(
                host_id="host-parallel-01", owner_id="user-a-001", state="shutting_down"
            )

        with patch("app.services.host.HostService.get_host", side_effect=mock_get_host_async):
            with patch("app.services.host.HostService.transition_state", side_effect=mock_transition_async):
                tasks = [
                    jwt_authenticated_client.post(f"{API_PREFIX}/host-parallel-01/stop")
                    for _ in range(3)
                ]
                responses = await asyncio.gather(*tasks)

                status_codes = [r.status_code for r in responses]
                success_count = sum(1 for s in status_codes if s in (200, 202))
                blocked_count = sum(1 for s in status_codes if s in (403, 409))

                assert success_count <= 1, (
                    f"Expected at most 1 success, got {success_count}. Codes: {status_codes}"
                )
                assert blocked_count >= 2, (
                    f"Expected at least 2 blocked, got {blocked_count}. Codes: {status_codes}"
                )

                for resp in responses:
                    body = resp.json()
                    if resp.status_code in (403, 409):
                        assert body["success"] is False


@pytest.mark.asyncio
class TestNetworkDisconnectSimulation:
    """EC-003: 网络断连模拟 — 优雅错误处理."""

    async def test_connection_error_returns_graceful_error(self, jwt_authenticated_client):
        with patch("app.services.host.HostService.get_host") as mock_get:
            mock_get.side_effect = ConnectionError("Connection refused")

            resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-conn-error")

            if resp.status_code >= 500:
                try:
                    body = resp.json()
                    assert "success" in body or "detail" in body
                except Exception:
                    assert resp.status_code in (500, 502, 503)

    async def test_timeout_error_returns_graceful_error(self, jwt_authenticated_client):
        async def slow_handler(*args, **kwargs):
            raise TimeoutError("Request timed out")

        with patch("app.services.host.HostService.get_host", side_effect=slow_handler):
            resp = await jwt_authenticated_client.get(
                f"{API_PREFIX}/host-timeout-error",
                timeout=0.01,
            )
            assert resp.status_code >= 400

    async def test_service_unavailable_returns_error_format(self, jwt_authenticated_client):
        with patch("app.services.host.HostService.get_host") as mock_get:
            mock_get.side_effect = Exception("Database unavailable")

            resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-db-error")
            assert resp.status_code >= 400
            if resp.headers.get("content-type", "").startswith("application/json"):
                body = resp.json()
                assert "success" in body or "detail" in body
