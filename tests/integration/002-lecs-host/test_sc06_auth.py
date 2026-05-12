"""
SC-06: API 认证与授权 — Integration Tests

TC-050: API 认证拦截 (401) — 无凭证、过期 JWT、伪造 JWT
TC-051: RBAC 授权 (403) — 普通用户仅见自身主机、管理员全量、越权拦截
"""

import pytest


API_PREFIX = "/api/v1/lecs-hosts"


def _make_valid_create_payload():
    return {
        "billing_mode": "包年/包月",
        "host_name": "test_host_auth",
        "username": "valid_user",
        "password": "Abcdef12!",
        "instance_type": "经济型",
        "instance_spec": "eco-001",
        "os_image": "Ubuntu 22.04 LTS",
        "ip_config": {"mode": "DHCP"},
        "duration": 1,
    }


# ====================================================================
# TC-050: API 认证拦截
# ====================================================================


@pytest.mark.asyncio
class TestNoAuth:
    """TC-050-01: 无认证凭证访问 API → 401."""

    async def test_get_hosts_without_auth_returns_401(self, api_client):
        resp = await api_client.get(API_PREFIX)
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert "error_code" in body
        assert "error_message" in body
        assert "data" not in body
        assert "application/json" in resp.headers.get("content-type", "")

    async def test_post_hosts_without_auth_returns_401(self, api_client):
        resp = await api_client.post(API_PREFIX, json=_make_valid_create_payload())
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False

    async def test_stop_without_auth_returns_401(self, api_client):
        resp = await api_client.post(f"{API_PREFIX}/fake-id/stop")
        assert resp.status_code == 401

    async def test_delete_without_auth_returns_401(self, api_client):
        resp = await api_client.delete(f"{API_PREFIX}/fake-id")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestExpiredJwt:
    """TC-050-02: 过期 JWT Cookie 访问 API → 401."""

    async def test_expired_jwt_get_hosts_returns_401(self, expired_jwt_client):
        resp = await expired_jwt_client.get(API_PREFIX)
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert "error_code" in body
        assert "error_message" in body

    async def test_expired_jwt_post_hosts_returns_401(self, expired_jwt_client):
        resp = await expired_jwt_client.post(API_PREFIX, json=_make_valid_create_payload())
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert "UNAUTHORIZED" in body.get("error_code", "") or "EXPIRED" in body.get("error_code", "") or "TOKEN" in body.get("error_code", "")


@pytest.mark.asyncio
class TestInvalidJwt:
    """TC-050-02: 伪造 JWT → 401."""

    async def test_invalid_jwt_get_hosts_returns_401(self, invalid_jwt_client):
        resp = await invalid_jwt_client.get(API_PREFIX)
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert "error_code" in body
        assert "error_message" in body

    async def test_invalid_jwt_stop_endpoint_returns_401(self, invalid_jwt_client):
        resp = await invalid_jwt_client.post(f"{API_PREFIX}/fake-id/stop")
        assert resp.status_code == 401

    async def test_invalid_jwt_delete_endpoint_returns_401(self, invalid_jwt_client):
        resp = await invalid_jwt_client.delete(f"{API_PREFIX}/fake-id")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestExpiredJwtOtherEndpoints:
    """TC-050-03: 过期 JWT 访问任意 API 端点 → 401."""

    async def test_expired_jwt_stop_returns_401(self, expired_jwt_client):
        resp = await expired_jwt_client.post(f"{API_PREFIX}/any-host-id/stop")
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False
        assert body.get("data") is None or "data" not in body

    async def test_expired_jwt_delete_returns_401(self, expired_jwt_client):
        resp = await expired_jwt_client.delete(f"{API_PREFIX}/any-host-id")
        assert resp.status_code == 401
        body = resp.json()
        assert body["success"] is False


# ====================================================================
# TC-051: RBAC 授权 — 用户只能访问自己的资源
# ====================================================================


@pytest.mark.asyncio
class TestNormalUserOwnHosts:
    """TC-051-01: 普通用户查询自身主机."""

    async def test_user_gets_own_hosts_only(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(
            API_PREFIX, params={"page": 1, "page_size": 50}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert body.get("pagination") is not None
        assert "total" in body.get("pagination", {})
        assert "page" in body.get("pagination", {})
        assert "page_size" in body.get("pagination", {})


@pytest.mark.asyncio
class TestAdminAllHosts:
    """TC-051-02: 管理员查询所有用户主机."""

    async def test_admin_gets_all_hosts(self, admin_authenticated_client):
        resp = await admin_authenticated_client.get(
            API_PREFIX, params={"page": 1, "page_size": 50}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "data" in body
        assert isinstance(body["data"], (list, type(None)))


@pytest.mark.asyncio
class TestHorizontalPrivilegeEscalation:
    """TC-051-03: 普通用户尝试访问他人主机 → 403."""

    async def test_user_get_other_user_host_returns_403(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(f"{API_PREFIX}/host-b-001")
        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert "error_code" in body
        assert "error_message" in body
        assert "FORBIDDEN" in body.get("error_code", "") or "RBAC" in body.get("error_code", "")

    async def test_user_stop_other_user_host_returns_403(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-b-001/stop")
        assert resp.status_code == 403

    async def test_user_delete_other_user_host_returns_403(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.delete(f"{API_PREFIX}/host-b-001")
        assert resp.status_code == 403

    async def test_filter_by_other_users_id_returns_403(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(
            API_PREFIX, params={"user_id": "other-user-id"}
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False


@pytest.mark.asyncio
class TestServiceTokenAuth:
    """Service Token 认证 — 非浏览器客户端访问 API."""

    async def test_service_token_get_hosts_allowed(self, service_token_client):
        resp = await service_token_client.get(API_PREFIX)
        assert resp.status_code == 200, f"Service token auth failed: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["success"] is True

    async def test_service_token_post_hosts_allowed(self, service_token_client):
        resp = await service_token_client.post(API_PREFIX, json=_make_valid_create_payload())
        assert resp.status_code in (201, 202), f"Expected 201/202, got {resp.status_code}"
        body = resp.json()
        assert body["success"] is True

    async def test_valid_jwt_cookie_access_allowed(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(API_PREFIX)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
