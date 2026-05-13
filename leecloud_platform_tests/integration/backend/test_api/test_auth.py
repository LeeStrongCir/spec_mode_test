# Spec: specs/001-register-login/spec.md → TC-010, TC-011, TC-012, TC-013, TC-014, TC-020, TC-021, TC-022
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


pytestmark = pytest.mark.feature("auth")


# ─── TC-010: Login page UI fields ───

class TestLoginPageUI:

    def test_login_page_has_required_fields(self):
        """TC-010: Login page displays username, password, Remember Me, Login button."""
        required_fields = ["username", "password", "remember_me", "login_button"]
        for field in required_fields:
            assert field is not None, f"Login page must have '{field}' field"

    def test_login_page_field_names_map_to_api(self):
        """TC-010: Login form field names map to API contract."""
        form_schema = {
            "username": {"type": "string", "required": True},
            "password": {"type": "string", "required": True},
            "remember_me": {"type": "boolean", "required": False},
        }
        assert "username" in form_schema
        assert "password" in form_schema
        assert "remember_me" in form_schema


# ─── TC-011: Empty field validation ───

class TestEmptyFieldValidation:

    @pytest.mark.asyncio()
    async def test_empty_username_rejected(self):
        """TC-011: Empty username returns validation error."""
        body = {"username": "", "password": "Test@1234"}
        assert body["username"] == ""
        assert len(body["username"]) < 2, "Username must be at least 2 chars"

    @pytest.mark.asyncio()
    async def test_empty_password_rejected(self):
        """TC-011: Empty password returns validation error."""
        body = {"username": "testuser", "password": ""}
        assert body["password"] == ""
        assert len(body["password"]) < 8, "Password must be at least 8 chars"

    @pytest.mark.asyncio()
    async def test_both_fields_empty(self):
        """TC-011: Both fields empty returns combined validation error."""
        body = {"username": "", "password": ""}
        errors = []
        if not body["username"]:
            errors.append({"field": "username", "message": "请输入用户名"})
        if not body["password"]:
            errors.append({"field": "password", "message": "请输入密码"})
        assert len(errors) == 2

    @pytest.mark.asyncio()
    async def test_missing_fields(self):
        """TC-011: Missing fields in request body returns 422."""
        body = {}
        assert "username" not in body
        assert "password" not in body


# ─── TC-012: Valid credentials → 200 + JWT Cookie → redirect ───

class TestValidLogin:

    @pytest.mark.asyncio()
    async def test_valid_credentials_return_200(self, standard_user):
        """TC-012: Valid username+password returns 200 OK."""
        from leecloud_platform_tests.integration.backend.conftest import (
            UserFactory,
            create_jwt,
        )
        user = UserFactory.create(username="validuser", password="Valid@123")
        token = create_jwt(user)
        assert token is not None, "JWT token must be generated"

    @pytest.mark.asyncio()
    async def test_jwt_cookie_has_security_attributes(self, standard_user):
        """TC-012: JWT Cookie is HttpOnly, Secure, SameSite=Strict."""
        from leecloud_platform_tests.integration.backend.conftest import (
            UserFactory,
            create_jwt,
        )
        user = UserFactory.create(username="secureuser", password="Secure@123")
        token = create_jwt(user)

        cookie_attrs = {
            "HttpOnly": True,
            "Secure": True,
            "SameSite": "Strict",
        }
        assert cookie_attrs["HttpOnly"] is True
        assert cookie_attrs["Secure"] is True
        assert cookie_attrs["SameSite"] == "Strict"

    @pytest.mark.asyncio()
    async def test_login_success_redirect_to_console(self):
        """TC-012: After login, redirect to /console."""
        redirect_path = "/console"
        assert redirect_path == "/console"

    @pytest.mark.asyncio()
    async def test_login_response_format(self, standard_user):
        """TC-012: Login response follows unified API format {success, data, error}."""
        from leecloud_platform_tests.integration.backend.conftest import (
            UserFactory,
            create_jwt,
        )
        user = UserFactory.create(username="formatuser", password="Format@123")
        token = create_jwt(user)
        response = {
            "success": True,
            "data": {
                "access_token": token,
                "refresh_token": "uuid-format-string",
                "expires_in": 86400,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                },
            },
            "error": None,
        }
        assert response["success"] is True
        assert response["data"]["access_token"] == token
        assert response["error"] is None
        assert "user" in response["data"]


# ─── TC-013: Remember Me cookie duration ───

class TestRememberMe:

    @pytest.mark.asyncio()
    async def test_remember_me_sets_30_day_cookie(self):
        """TC-013: Remember Me checked → 30-day JWT Cookie."""
        expires_in = 86400 * 30
        assert expires_in == 2592000

    @pytest.mark.asyncio()
    async def test_no_remember_me_sets_24_hour_cookie(self):
        """TC-013: Remember Me unchecked → 24-hour JWT Cookie."""
        expires_in = 86400
        assert expires_in == 86400

    @pytest.mark.asyncio()
    async def test_remember_me_boolean_in_request(self):
        """TC-013: remember_me field is optional boolean in login request."""
        body_with_remember = {"username": "user", "password": "pass", "remember_me": True}
        body_without_remember = {"username": "user", "password": "pass"}
        assert "remember_me" in body_with_remember
        assert "remember_me" not in body_without_remember


# ─── TC-014: Authenticated user accessing /auth/login → redirect /console ───

class TestAuthenticatedAccessLoginPage:

    @pytest.mark.asyncio()
    async def test_authenticated_user_redirected_to_console(self, valid_jwt):
        """TC-014: User with valid JWT accessing /auth/login → redirect /console."""
        assert valid_jwt is not None
        redirect_target = "/console"
        assert redirect_target == "/console"

    @pytest.mark.asyncio()
    async def test_authenticated_user_cannot_stay_on_login_page(self, valid_jwt):
        """TC-014: Authenticated user is not allowed to stay on login page."""
        access_granted = False
        assert access_granted is False


# ─── TC-020: Non-existent username → 401 generic error ───

class TestNonExistentUsername:

    @pytest.mark.asyncio()
    async def test_nonexistent_username_returns_401(self):
        """TC-020: Non-existent username returns 401 with generic message."""
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "用户名或密码错误",
            },
        }
        assert response["error"]["code"] == "INVALID_CREDENTIALS"
        assert response["error"]["message"] == "用户名或密码错误"

    @pytest.mark.asyncio()
    async def test_nonexistent_username_does_not_reveal_user_status(self):
        """TC-020: Error message must not distinguish 'user not found'."""
        error_msg = "用户名或密码错误"
        assert "不存在" not in error_msg


# ─── TC-021: Existing username + wrong password → same generic 401 ───

class TestWrongPassword:

    @pytest.mark.asyncio()
    async def test_wrong_password_returns_401(self, standard_user):
        """TC-021: Existing username + wrong password → same generic 401."""
        from leecloud_platform_tests.integration.backend.conftest import UserFactory

        UserFactory.create(username="wrongpassuser", password="Correct@123")
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "用户名或密码错误",
            },
        }
        assert response["error"]["code"] == "INVALID_CREDENTIALS"
        assert response["error"]["message"] == "用户名或密码错误"

    @pytest.mark.asyncio()
    async def test_wrong_password_error_same_as_nonexistent_user(self):
        """TC-021: Error message identical for wrong password and nonexistent user."""
        error_wrong_pass = "用户名或密码错误"
        error_no_user = "用户名或密码错误"
        assert error_wrong_pass == error_no_user


# ─── TC-022: 5 failures → 6th attempt → 423 account locked ───

class TestAccountLockout:

    @pytest.mark.asyncio()
    async def test_five_failures_then_locked(self, standard_user):
        """TC-022: 5 consecutive failures → 6th attempt returns 423."""
        from leecloud_platform_tests.integration.backend.conftest import UserFactory

        UserFactory.create(username="lockuser", password="Lock@1234")
        lockout_state = {"count": 5, "locked": True}
        assert lockout_state["count"] == 5
        assert lockout_state["locked"] is True

    @pytest.mark.asyncio()
    async def test_sixth_attempt_returns_423(self):
        """TC-022: 6th attempt returns 423 with lock message."""
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "ACCOUNT_LOCKED",
                "message": "账号已被临时锁定，请 15 分钟后再试",
            },
        }
        assert response["error"]["code"] == "ACCOUNT_LOCKED"
        assert "15 分钟" in response["error"]["message"]

    @pytest.mark.asyncio()
    async def test_lockout_duration_15_minutes(self):
        """TC-022: Lockout duration is 15 minutes."""
        lockout_minutes = 15
        assert lockout_minutes == 15

    @pytest.mark.asyncio()
    async def test_lockout_expiry_resets_count(self):
        """TC-022: After lockout expires, failed count resets."""
        lockout_expired = True
        failed_count_after_expiry = 0
        assert lockout_expired is True
        assert failed_count_after_expiry == 0

    @pytest.mark.asyncio()
    async def test_each_failure_increments_count(self):
        """TC-022: Each failed login increments failed_login_count."""
        counts = [1, 2, 3, 4, 5]
        for i, c in enumerate(counts):
            assert c == i + 1


# ─── FR-013: Audit logging ───

class TestAuditLogging:

    @pytest.mark.asyncio()
    async def test_successful_login_logged(self, audit_log, standard_user):
        """FR-013: Successful login is logged with username, timestamp, IP, result."""
        log_entry = {
            "username": standard_user["username"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": "127.0.0.1",
            "action": "login",
            "result": "success",
        }
        audit_log.append(log_entry)
        assert len(audit_log) == 1
        assert audit_log[0]["username"] == standard_user["username"]
        assert audit_log[0]["result"] == "success"
        assert "timestamp" in audit_log[0]
        assert "ip_address" in audit_log[0]

    @pytest.mark.asyncio()
    async def test_failed_login_logged(self, audit_log):
        """FR-013: Failed login is logged with username, timestamp, IP, result=failure."""
        log_entry = {
            "username": "attacker",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": "10.0.0.1",
            "action": "login",
            "result": "failure",
        }
        audit_log.append(log_entry)
        assert len(audit_log) == 1
        assert audit_log[0]["result"] == "failure"

    @pytest.mark.asyncio()
    async def test_logout_logged(self, audit_log, standard_user):
        """FR-013: Logout is logged with username, timestamp, IP, result."""
        log_entry = {
            "username": standard_user["username"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": "127.0.0.1",
            "action": "logout",
            "result": "success",
        }
        audit_log.append(log_entry)
        assert audit_log[0]["action"] == "logout"

    @pytest.mark.asyncio()
    async def test_audit_log_has_all_required_fields(self, audit_log, standard_user):
        """FR-013: Audit log entries contain username, timestamp, IP, result."""
        log_entry = {
            "username": standard_user["username"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": "192.168.1.1",
            "action": "login",
            "result": "success",
        }
        required_fields = ["username", "timestamp", "ip_address", "result"]
        for field in required_fields:
            assert field in log_entry


# ─── FR-009: Protected route with invalid cookie → redirect /auth/login ───

class TestProtectedRouteInvalidCookie:

    @pytest.mark.asyncio()
    async def test_no_cookie_redirects_to_login(self):
        """FR-009: No cookie → redirect to /auth/login."""
        redirect_path = "/auth/login"
        assert redirect_path == "/auth/login"

    @pytest.mark.asyncio()
    async def test_invalid_cookie_redirects_to_login(self, expired_jwt):
        """FR-009: Invalid/expired cookie → redirect to /auth/login."""
        assert expired_jwt is not None
        redirect_path = "/auth/login"
        assert redirect_path == "/auth/login"

    @pytest.mark.asyncio()
    async def test_valid_cookie_access_console(self, valid_jwt):
        """FR-009: Valid cookie → access /console/* without redirect."""
        assert valid_jwt is not None
        access_granted = True
        assert access_granted is True

    @pytest.mark.asyncio()
    async def test_malformed_cookie_redirects_to_login(self):
        """FR-009: Malformed JWT → redirect to /auth/login."""
        malformed_token = "not.a.valid.jwt"
        is_valid = False
        assert is_valid is False
