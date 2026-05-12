"""
SC-07: 统一响应格式 — Integration Tests

TC-052: 所有 API 端点返回一致的 JSON 响应结构
- 成功: { success: true, data: ... }
- 校验失败: { success: false, error_code, error_message, errors }
- 资源不存在: { success: false, error_code: "NOT_FOUND", ... }
- 状态冲突: { success: false, error_code: "CONFLICT", ... }
"""

import pytest


API_PREFIX = "/api/v1/lecs-hosts"


def _make_valid_create_payload():
    return {
        "billing_mode": "包年/包月",
        "host_name": "test_host_resp",
        "username": "valid_user",
        "password": "Abcdef12!",
        "instance_type": "经济型",
        "instance_spec": "eco-001",
        "os_image": "Ubuntu 22.04 LTS",
        "ip_config": {"mode": "DHCP"},
        "duration": 1,
    }


# ====================================================================
# TC-052-01: 成功响应格式
# ====================================================================


@pytest.mark.asyncio
class TestSuccessResponseFormat:
    """TC-052-01: 成功响应统一格式验证."""

    async def test_get_hosts_success_format(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(
            API_PREFIX, params={"page": 1, "page_size": 10}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["success"], bool)
        assert body["success"] is True
        assert "data" in body
        assert isinstance(body["data"], (list, dict, type(None)))

    async def test_get_hosts_pagination_fields(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(
            API_PREFIX, params={"page": 1, "page_size": 10}
        )
        body = resp.json()
        pagination = body.get("pagination")
        if pagination is not None:
            assert "total" in pagination
            assert "page" in pagination
            assert "page_size" in pagination

    async def test_create_host_success_format(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(
            API_PREFIX, json=_make_valid_create_payload()
        )
        assert resp.status_code in (201, 202)
        body = resp.json()
        assert isinstance(body["success"], bool)
        assert body["success"] is True
        assert "data" in body
        data = body["data"]
        assert isinstance(data, dict)
        assert "id" in data or "host_name" in data or "status" in data


# ====================================================================
# TC-052-02: 校验失败响应格式
# ====================================================================


@pytest.mark.asyncio
class TestValidationErrorResponseFormat:
    """TC-052-02: 参数校验错误 → VALIDATION_ERROR."""

    async def test_missing_required_field_returns_validation_error(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(API_PREFIX, json={})
        assert resp.status_code == 400
        body = resp.json()
        assert isinstance(body["success"], bool)
        assert body["success"] is False
        assert isinstance(body["error_code"], str)
        assert isinstance(body["error_message"], str)

    async def test_invalid_hostname_returns_validation_error(self, jwt_authenticated_client):
        payload = _make_valid_create_payload()
        payload["host_name"] = "_abc"
        resp = await jwt_authenticated_client.post(API_PREFIX, json=payload)
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)
        assert isinstance(body["error_message"], str)

    async def test_validation_error_response_structure(self, jwt_authenticated_client):
        """验证校验失败响应可选的 errors 字段结构."""
        resp = await jwt_authenticated_client.post(API_PREFIX, json={})
        body = resp.json()
        assert "error_code" in body
        assert "error_message" in body
        if "errors" in body:
            assert isinstance(body["errors"], list)
            for err in body["errors"]:
                assert "field" in err
                assert "message" in err

    async def test_password_too_short_validation(self, jwt_authenticated_client):
        payload = _make_valid_create_payload()
        payload["password"] = "123"
        resp = await jwt_authenticated_client.post(API_PREFIX, json=payload)
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)

    async def test_username_too_short_validation(self, jwt_authenticated_client):
        payload = _make_valid_create_payload()
        payload["username"] = "ab"
        resp = await jwt_authenticated_client.post(API_PREFIX, json=payload)
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)


# ====================================================================
# TC-052-03: 资源不存在响应格式
# ====================================================================


@pytest.mark.asyncio
class TestNotFoundResponseFormat:
    """TC-052-03: 资源不存在 → NOT_FOUND."""

    async def test_get_nonexistent_host_returns_not_found(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(f"{API_PREFIX}/nonexistent-host-id-99999")
        assert resp.status_code == 404
        body = resp.json()
        assert isinstance(body["success"], bool)
        assert body["success"] is False
        assert isinstance(body["error_code"], str)
        assert isinstance(body["error_message"], str)
        assert "NOT_FOUND" in body["error_code"] or "NOT_FOUND" in body.get("error_message", "").upper()

    async def test_stop_nonexistent_host_returns_not_found(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(f"{API_PREFIX}/nonexistent-host-id-99999/stop")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)

    async def test_delete_nonexistent_host_returns_not_found(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.delete(f"{API_PREFIX}/nonexistent-host-id-99999")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)


# ====================================================================
# TC-052-04: 状态冲突响应格式
# ====================================================================


@pytest.mark.asyncio
class TestConflictResponseFormat:
    """TC-052-04: 状态冲突 → CONFLICT / STATE_CONFLICT."""

    async def test_stop_already_stopped_host_returns_conflict(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-stopped-01/stop")
        assert resp.status_code in (403, 409)
        body = resp.json()
        assert isinstance(body["success"], bool)
        assert body["success"] is False
        assert isinstance(body["error_code"], str)
        assert isinstance(body["error_message"], str)

    async def test_start_normal_host_returns_conflict(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.post(f"{API_PREFIX}/host-normal-01/start")
        assert resp.status_code in (403, 409)
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["error_code"], str)
        assert isinstance(body["error_message"], str)


# ====================================================================
# Cross-endpoint consistency
# ====================================================================


@pytest.mark.asyncio
class TestResponseFormatConsistency:
    """所有端点返回一致的顶层字段结构."""

    async def test_all_error_responses_have_success_false_field(self, api_client):
        endpoints = [
            ("GET", API_PREFIX, None),
            ("POST", f"{API_PREFIX}/fake-id/stop", None),
            ("DELETE", f"{API_PREFIX}/fake-id", None),
            ("POST", API_PREFIX, {}),
        ]
        for method, url, body in endpoints:
            if method == "GET":
                resp = await api_client.get(url)
            elif method == "POST":
                resp = await api_client.post(url, json=body)
            elif method == "DELETE":
                resp = await api_client.delete(url)

            if resp.status_code >= 400:
                error_body = resp.json()
                assert "success" in error_body, f"Missing 'success' in {method} {url}"
                assert error_body["success"] is False, f"'success' not false in {method} {url}"

    async def test_success_is_boolean_type(self, jwt_authenticated_client):
        resp = await jwt_authenticated_client.get(API_PREFIX, params={"page": 1, "page_size": 10})
        assert isinstance(resp.json()["success"], bool)

    async def test_error_code_is_string_type(self, expired_jwt_client):
        resp = await expired_jwt_client.get(API_PREFIX)
        body = resp.json()
        assert isinstance(body["error_code"], str)

    async def test_error_message_is_string_type(self, expired_jwt_client):
        resp = await expired_jwt_client.get(API_PREFIX)
        body = resp.json()
        assert isinstance(body["error_message"], str)
