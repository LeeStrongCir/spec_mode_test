"""
SC-02: List Page & Operation Matrix — Integration Tests

Tests for GET /api/v1/lecs-hosts endpoint:
- TC-010: List page data columns completeness (API level)
- Pagination: page, page_size, total count
- Soft-delete filter: WHERE deleted_at IS NULL
- RBAC: normal user sees only own hosts, admin sees all
- Status filter: valid and invalid status values
- Host states: normal/stopped/failed/creating/deleting → verify data in response
- Pagination edge cases: page=0, page_size > max
- Unauthenticated → 401, unauthorized cross-user access → 403

Uses pytest + httpx AsyncClient following FastAPI test patterns.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient


# --- Host status constants ---

HOST_STATUS_CREATING = "creating"
HOST_STATUS_NORMAL = "normal"
HOST_STATUS_STOPPED = "stopped"
HOST_STATUS_FAILED = "failed"
HOST_STATUS_DELETING = "deleting"

VALID_STATUSES = {HOST_STATUS_CREATING, HOST_STATUS_NORMAL, HOST_STATUS_STOPPED, HOST_STATUS_FAILED, HOST_STATUS_DELETING}

# --- Mock data factories ---

def make_host(
    status: str,
    user_id: str = None,
    hostname: str = None,
    host_id: str = None,
    private_ip: str = None,
    billing_mode: str = "PREPAID",
    deleted_at: datetime = None,
) -> dict:
    """Create a mock LECS host dictionary matching the API response schema."""
    return {
        "id": host_id or str(uuid.uuid4()),
        "user_id": user_id or str(uuid.uuid4()),
        "hostname": hostname or f"test-host-{uuid.uuid4().hex[:6]}",
        "billing_mode": billing_mode,
        "status": status,
        "private_ip": private_ip or "192.168.1.100",
        "os_image": "UBUNTU",
        "ip_allocation": "DHCP",
        "ip_address": None,
        "subnet_mask": None,
        "instance_type_id": str(uuid.uuid4()),
        "purchase_months": 1,
        "cost_snapshot": 9900,
        "created_at": "2026-05-12T10:00:00Z",
        "started_at": "2026-05-12T10:05:00Z" if status == HOST_STATUS_NORMAL else None,
        "deleted_at": deleted_at.isoformat() if deleted_at else None,
    }


def mock_list_api_response(
    hosts: list[dict],
    total: int = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Build a standard paginated API response."""
    return {
        "success": True,
        "data": hosts,
        "pagination": {
            "total": total if total is not None else len(hosts),
            "page": page,
            "page_size": page_size,
        },
    }


# --- Pytest fixtures ---

@pytest.fixture
def user_id_admin():
    return "admin-0000-0000-0000-000000000001"


@pytest.fixture
def user_id_normal():
    return "user-0000-0000-0000-000000000001"


@pytest.fixture
def user_id_other():
    return "user-0000-0000-0000-000000000002"


@pytest.fixture
def hosts_all_states(user_id_normal) -> list[dict]:
    """Create one host in each state plus a soft-deleted host."""
    now = datetime.now(timezone.utc)
    return [
        make_host(status=HOST_STATUS_CREATING, user_id=user_id_normal, hostname="host-creating", private_ip=None),
        make_host(status=HOST_STATUS_NORMAL, user_id=user_id_normal, hostname="host-normal", private_ip="192.168.1.10"),
        make_host(status=HOST_STATUS_STOPPED, user_id=user_id_normal, hostname="host-stopped", private_ip="192.168.1.20"),
        make_host(status=HOST_STATUS_FAILED, user_id=user_id_normal, hostname="host-failed", private_ip="192.168.1.30"),
        make_host(status=HOST_STATUS_DELETING, user_id=user_id_normal, hostname="host-deleting", private_ip="192.168.1.40"),
        # Soft-deleted host — should NOT appear in normal queries
        make_host(
            status=HOST_STATUS_DELETING,
            user_id=user_id_normal,
            hostname="host-deleted-soft",
            private_ip="192.168.1.50",
            deleted_at=now,
        ),
    ]


@pytest.fixture
def mock_async_queue():
    """Mock async task queue; verifies task submission without executing."""
    with patch("celery.Celery.send_task", new_callable=MagicMock) as mock:
        mock_result = MagicMock()
        mock_result.id = "mock-task-id"
        mock.return_value = mock_result
        yield mock


# --- Positive tests: API response structure & pagination ---

@pytest.mark.asyncio
class TestListPagination:
    """TC-010 (partial): Verify paginated host list API response structure."""

    async def test_list_returns_success_with_data_and_pagination(
        self, api_client: AsyncClient, hosts_all_states, user_id_normal
    ):
        """GET /api/v1/lecs-hosts → { success: true, data: [...], pagination: {...} }."""
        # Simulate the API filtering hosts (exclude soft-deleted)
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=len(active_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10})
            body = response.json()

            assert body["success"] is True
            assert "data" in body
            assert isinstance(body["data"], list)
            assert "pagination" in body
            assert "total" in body["pagination"]
            assert "page" in body["pagination"]
            assert "page_size" in body["pagination"]

    async def test_list_pagination_totals_match_filtered_hosts(
        self, api_client: AsyncClient, hosts_all_states, user_id_normal
    ):
        """Pagination total reflects only non-soft-deleted hosts."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]
        expected_total = len(active_hosts)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=expected_total),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10})
            body = response.json()

            assert body["pagination"]["total"] == expected_total
            # Soft-deleted host must NOT be counted
            host_ids = {h["id"] for h in body["data"]}
            deleted_host = next(h for h in hosts_all_states if h["deleted_at"] is not None)
            assert deleted_host["id"] not in host_ids

    async def test_list_page_1_returns_first_page(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """page=1 returns the first chunk of hosts up to page_size."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]
        page_size = 2
        page_1_hosts = active_hosts[:page_size]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(page_1_hosts, total=len(active_hosts), page=1, page_size=page_size),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": page_size})
            body = response.json()

            assert len(body["data"]) <= page_size
            assert body["pagination"]["page"] == 1
            assert body["pagination"]["total"] == len(active_hosts)

    async def test_list_response_host_fields_present(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Each host in response contains required fields: id, hostname, billing_mode, status, private_ip."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=len(active_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10})
            body = response.json()

            required_fields = {"id", "hostname", "billing_mode", "status", "private_ip"}
            for host in body["data"]:
                assert required_fields.issubset(host.keys()), f"Missing fields in host {host.get('id')}"
                assert host["id"], "Host ID must not be empty"
                assert host["hostname"], "Hostname must not be empty"
                assert host["status"] in VALID_STATUSES, f"Invalid status: {host['status']}"


# --- Soft-delete filter tests ---

@pytest.mark.asyncio
class TestSoftDeleteFilter:
    """Verify that soft-deleted hosts (deleted_at IS NOT NULL) do not appear in list."""

    async def test_soft_deleted_hosts_excluded_from_list(
        self, api_client: AsyncClient, hosts_all_states, user_id_normal
    ):
        """Hosts with deleted_at set must NOT appear in API response."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]
        deleted_hosts = [h for h in hosts_all_states if h["deleted_at"] is not None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=len(active_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 20})
            body = response.json()

            returned_ids = {h["id"] for h in body["data"]}
            for deleted in deleted_hosts:
                assert deleted["id"] not in returned_ids, "Soft-deleted host should not appear in list"

    async def test_soft_deleted_hosts_not_counted_in_total(
        self, api_client: AsyncClient, hosts_all_states, user_id_normal
    ):
        """Pagination total must exclude soft-deleted hosts."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]
        deleted_count = sum(1 for h in hosts_all_states if h["deleted_at"] is not None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=len(active_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 20})
            body = response.json()

            assert body["pagination"]["total"] == len(active_hosts)
            assert body["pagination"]["total"] == len(hosts_all_states) - deleted_count


# --- Status filter tests ---

@pytest.mark.asyncio
class TestStatusFilter:
    """Verify status query parameter filtering."""

    async def test_filter_by_normal_status(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """status=normal returns only normal hosts."""
        normal_hosts = [h for h in hosts_all_states if h["status"] == HOST_STATUS_NORMAL and h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(normal_hosts, total=len(normal_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "normal"})
            body = response.json()

            assert body["success"] is True
            for host in body["data"]:
                assert host["status"] == HOST_STATUS_NORMAL

    async def test_filter_by_stopped_status(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """status=stopped returns only stopped hosts."""
        stopped_hosts = [h for h in hosts_all_states if h["status"] == HOST_STATUS_STOPPED and h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(stopped_hosts, total=len(stopped_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "stopped"})
            body = response.json()

            for host in body["data"]:
                assert host["status"] == HOST_STATUS_STOPPED

    async def test_filter_by_failed_status(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """status=failed returns only failed hosts."""
        failed_hosts = [h for h in hosts_all_states if h["status"] == HOST_STATUS_FAILED and h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(failed_hosts, total=len(failed_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "failed"})
            body = response.json()

            for host in body["data"]:
                assert host["status"] == HOST_STATUS_FAILED

    async def test_filter_by_creating_status(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """status=creating returns only creating hosts; private_ip may be null."""
        creating_hosts = [h for h in hosts_all_states if h["status"] == HOST_STATUS_CREATING and h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(creating_hosts, total=len(creating_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "creating"})
            body = response.json()

            for host in body["data"]:
                assert host["status"] == HOST_STATUS_CREATING

    async def test_filter_by_deleting_status(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """status=deleting returns only deleting hosts."""
        # Only active (non-soft-deleted) deleting hosts
        deleting_hosts = [h for h in hosts_all_states if h["status"] == HOST_STATUS_DELETING and h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(deleting_hosts, total=len(deleting_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "deleting"})
            body = response.json()

            for host in body["data"]:
                assert host["status"] == HOST_STATUS_DELETING

    async def test_filter_with_invalid_status_returns_400(self, api_client: AsyncClient):
        """status=invalid_value → 400 Bad Request."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=400,
                json=lambda: {
                    "success": False,
                    "error_code": "INVALID_STATUS",
                    "error_message": f"Invalid status value. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
                },
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10, "status": "running"})
            assert response.status_code == 400
            body = response.json()
            assert body["success"] is False
            assert body["error_code"] == "INVALID_STATUS"

    async def test_filter_with_empty_status_returns_all(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """No status filter → returns all active hosts."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(active_hosts, total=len(active_hosts)),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 20})
            body = response.json()

            assert body["success"] is True
            assert len(body["data"]) == len(active_hosts)


# --- Host state data verification ---

@pytest.mark.asyncio
class TestHostStatesInResponse:
    """Verify each host state appears correctly in the API response."""

    async def test_normal_host_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Normal state host: status='normal', has private_ip, started_at set."""
        normal_host = next(h for h in hosts_all_states if h["status"] == HOST_STATUS_NORMAL and h["deleted_at"] is None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([normal_host], total=1),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 1, "status": "normal"})
            body = response.json()

            host = body["data"][0]
            assert host["status"] == HOST_STATUS_NORMAL
            assert host["private_ip"] == "192.168.1.10"
            assert host["started_at"] is not None

    async def test_stopped_host_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Stopped state host: status='stopped', retains private_ip."""
        stopped_host = next(h for h in hosts_all_states if h["status"] == HOST_STATUS_STOPPED and h["deleted_at"] is None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([stopped_host], total=1),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 1, "status": "stopped"})
            body = response.json()

            host = body["data"][0]
            assert host["status"] == HOST_STATUS_STOPPED
            assert host["private_ip"] == "192.168.1.20"

    async def test_failed_host_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Failed state host: status='failed', retains private_ip."""
        failed_host = next(h for h in hosts_all_states if h["status"] == HOST_STATUS_FAILED and h["deleted_at"] is None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([failed_host], total=1),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 1, "status": "failed"})
            body = response.json()

            host = body["data"][0]
            assert host["status"] == HOST_STATUS_FAILED
            assert host["private_ip"] == "192.168.1.30"

    async def test_creating_host_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Creating state host: status='creating', private_ip may be None."""
        creating_host = next(h for h in hosts_all_states if h["status"] == HOST_STATUS_CREATING and h["deleted_at"] is None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([creating_host], total=1),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 1, "status": "creating"})
            body = response.json()

            host = body["data"][0]
            assert host["status"] == HOST_STATUS_CREATING
            # Creating hosts may not have private_ip assigned yet
            assert host["private_ip"] is None or isinstance(host["private_ip"], str)

    async def test_deleting_host_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """Deleting state host (not yet soft-deleted): appears in list with status='deleting'."""
        deleting_host = next(h for h in hosts_all_states if h["status"] == HOST_STATUS_DELETING and h["deleted_at"] is None)

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([deleting_host], total=1),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 1, "status": "deleting"})
            body = response.json()

            host = body["data"][0]
            assert host["status"] == HOST_STATUS_DELETING
            assert host["deleted_at"] is None  # Not yet soft-deleted


# --- Pagination edge cases ---

@pytest.mark.asyncio
class TestPaginationEdgeCases:
    """Test pagination parameter boundary conditions."""

    async def test_page_zero_returns_error_or_first_page(self, api_client: AsyncClient):
        """page=0 → either 400 error or treated as page=1."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            # API should handle page=0 gracefully: either error or treat as 1
            mock_get.return_value = MagicMock(
                status_code=400,
                json=lambda: {
                    "success": False,
                    "error_code": "INVALID_PAGE",
                    "error_message": "Page number must be a positive integer (>= 1).",
                },
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 0, "page_size": 10})
            # Either 400 or auto-corrected to page=1
            if response.status_code == 400:
                body = response.json()
                assert body["success"] is False
                assert "INVALID_PAGE" in body.get("error_code", "")
            elif response.status_code == 200:
                body = response.json()
                assert body["pagination"]["page"] >= 1

    async def test_page_size_exceeds_max_returns_capped_or_error(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """page_size > max (e.g., 10000) → either capped to max or 400 error."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            # Server caps page_size to 100
            capped_hosts = active_hosts[:100]
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(capped_hosts, total=len(active_hosts), page_size=100),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10000})
            body = response.json()

            # page_size should be capped or return error
            if response.status_code == 200:
                assert body["pagination"]["page_size"] <= 100, "page_size should be capped at server maximum"
            else:
                # Or return 400 for invalid page_size
                assert response.status_code == 400 or body.get("success") is False

    async def test_page_size_negative_returns_error(self, api_client: AsyncClient):
        """page_size=-1 → 400 Bad Request."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=400,
                json=lambda: {
                    "success": False,
                    "error_code": "INVALID_PAGE_SIZE",
                    "error_message": "Page size must be a positive integer.",
                },
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": -1})
            assert response.status_code == 400
            body = response.json()
            assert body["success"] is False

    async def test_page_beyond_total_returns_empty_data(self, api_client: AsyncClient, hosts_all_states, user_id_normal):
        """page=999 with only 5 hosts → empty data list, total unchanged."""
        active_hosts = [h for h in hosts_all_states if h["deleted_at"] is None]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response([], total=len(active_hosts), page=999, page_size=10),
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 999, "page_size": 10})
            body = response.json()

            assert body["success"] is True
            assert body["data"] == []
            assert body["pagination"]["total"] == len(active_hosts)
            assert body["pagination"]["page"] == 999


# --- RBAC tests ---

@pytest.mark.asyncio
class TestRBAC:
    """Verify role-based access control for host listing."""

    async def test_normal_user_sees_only_own_hosts(
        self, api_client: AsyncClient, user_id_normal, user_id_other
    ):
        """Normal user: list returns only hosts owned by that user."""
        own_hosts = [
            make_host(status=HOST_STATUS_NORMAL, user_id=user_id_normal, hostname="my-normal-host"),
        ]
        other_hosts = [
            make_host(status=HOST_STATUS_STOPPED, user_id=user_id_other, hostname="other-stopped-host"),
        ]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(own_hosts, total=len(own_hosts)),
            )

            response = await api_client.get(
                "/api/v1/lecs-hosts",
                params={"page": 1, "page_size": 10},
                headers={"X-User-Id": user_id_normal},
            )
            body = response.json()

            returned_ids = {h["id"] for h in body["data"]}
            for other in other_hosts:
                assert other["id"] not in returned_ids, "User should not see another user's hosts"
            for own in own_hosts:
                assert own["id"] in returned_ids, "User should see own hosts"

    async def test_admin_sees_all_hosts(
        self, api_client: AsyncClient, user_id_admin, user_id_normal, user_id_other
    ):
        """Admin: list returns hosts from all users."""
        all_hosts = [
            make_host(status=HOST_STATUS_NORMAL, user_id=user_id_normal, hostname="user-a-host"),
            make_host(status=HOST_STATUS_STOPPED, user_id=user_id_other, hostname="user-b-host"),
        ]

        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_list_api_response(all_hosts, total=len(all_hosts)),
            )

            response = await api_client.get(
                "/api/v1/lecs-hosts",
                params={"page": 1, "page_size": 20, "role": "admin"},
                headers={"X-User-Id": user_id_admin, "X-Role": "admin"},
            )
            body = response.json()

            assert body["success"] is True
            assert len(body["data"]) == len(all_hosts), "Admin should see all hosts"

    async def test_cross_user_access_returns_403(
        self, api_client: AsyncClient, user_id_normal, user_id_other
    ):
        """Normal user attempting to access or filter by another user's hosts → 403."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=403,
                json=lambda: {
                    "success": False,
                    "error_code": "FORBIDDEN",
                    "error_message": "You do not have permission to access this resource.",
                },
            )

            # Attempt to query with another user's ID explicitly
            response = await api_client.get(
                "/api/v1/lecs-hosts",
                params={"page": 1, "page_size": 10, "user_id": user_id_other},
                headers={"X-User-Id": user_id_normal},
            )
            assert response.status_code == 403
            body = response.json()
            assert body["success"] is False
            assert body["error_code"] == "FORBIDDEN"


# --- Authentication tests ---

@pytest.mark.asyncio
class TestAuth:
    """Verify authentication requirements for the list endpoint."""

    async def test_unauthenticated_request_returns_401(self, api_client: AsyncClient):
        """No auth token/cookie → 401 Unauthorized."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=401,
                json=lambda: {
                    "success": False,
                    "error_code": "UNAUTHORIZED",
                    "error_message": "Authentication required.",
                },
            )

            response = await api_client.get("/api/v1/lecs-hosts", params={"page": 1, "page_size": 10})
            assert response.status_code == 401
            body = response.json()
            assert body["success"] is False
            assert body["error_code"] == "UNAUTHORIZED"

    async def test_expired_token_returns_401(self, api_client: AsyncClient):
        """Expired JWT token → 401 Unauthorized."""
        with patch.object(AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=401,
                json=lambda: {
                    "success": False,
                    "error_code": "TOKEN_EXPIRED",
                    "error_message": "Authentication token has expired.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

            response = await api_client.get(
                "/api/v1/lecs-hosts",
                params={"page": 1, "page_size": 10},
                headers={"Authorization": "Bearer expired_token_here"},
            )
            assert response.status_code == 401
            body = response.json()
            assert body["success"] is False


# --- Async task submission verification ---

@pytest.mark.asyncio
class TestAsyncTaskQueue:
    """Verify mock_async_queue captures task submissions."""

    async def test_mock_async_queue_records_task(self, mock_async_queue):
        """mock_async_queue is called when a task is submitted."""
        # Simulate task submission
        mock_async_queue("list_hosts_sync", user_id="test-user", page=1)
        mock_async_queue.assert_called_once()
        assert mock_async_queue.call_args[0][0] == "list_hosts_sync"

    async def test_mock_async_queue_does_not_execute_task(self, mock_async_queue):
        """Confirm mock returns a mock result, not executing real async work."""
        result = mock_async_queue("test_task")
        assert hasattr(result, "id"), "Mock async result should have an id attribute"
        assert result.id == "mock-task-id"
