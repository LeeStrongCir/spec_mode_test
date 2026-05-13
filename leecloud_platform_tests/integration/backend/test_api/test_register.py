# Spec: specs/001-register-login/spec.md → TC-001-TC-008, EC-003, EC-004
# Backend Integration Tests: Register API (FR-014 ~ FR-021)

import re

import pytest
import pytest_asyncio


pytestmark = [pytest.mark.asyncio(loop_scope="function"), pytest.mark.feature("register")]


# ─── TC-001: Register page UI fields ───────────────────────────────────────────

class TestRegisterPageUI:
    """TC-001: Verify register page renders with all required form fields."""

    async def test_register_page_has_username_input(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert 'name="username"' in resp.text or 'id="username"' in resp.text

    async def test_register_page_has_password_input(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert 'name="password"' in resp.text or 'id="password"' in resp.text

    async def test_register_page_has_confirm_password_input(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert 'name="confirm_password"' in resp.text or 'id="confirm_password"' in resp.text

    async def test_register_page_has_email_input(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert 'name="email"' in resp.text or 'id="email"' in resp.text

    async def test_register_page_has_submit_button(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        # "注册" button rendered in form
        assert "注册" in resp.text

    async def test_register_page_has_login_link(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert "/auth/login" in resp.text

    async def test_register_page_sets_csrf_cookie(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        csrf_cookie = resp.cookies.get("csrf_token")
        assert csrf_cookie is not None
        assert len(csrf_cookie) > 0


# ─── TC-002: Empty/missing field validation ────────────────────────────────────

class TestEmptyFieldValidation:
    """TC-002: Required field empty-value validation."""

    async def test_register_all_empty_fields_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "", "password": "", "confirm_password": "", "email": ""},
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422

    async def test_register_missing_username_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "", "password": "Pass@123", "confirm_password": "Pass@123", "email": "a@b.com"},
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422

    async def test_register_missing_password_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "validuser", "password": "", "confirm_password": "Pass@123", "email": "a@b.com"},
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422

    async def test_register_missing_email_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": "validuser", "password": "Pass@123", "confirm_password": "Pass@123", "email": ""},
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422


# ─── TC-003: Duplicate username ────────────────────────────────────────────────

class TestDuplicateUsername:
    """TC-003: Register with existing username returns 409/422 error."""

    async def test_register_duplicate_username_returns_error(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]

        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "first@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )

        csrf_resp2 = await async_client.get("/api/v1/auth/csrf")
        csrf_token2 = csrf_resp2.json()["data"]["csrf_token"]

        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "Different@1",
                "confirm_password": "Different@1",
                "email": "second@example.com",
            },
            headers={"x-csrf-token": csrf_token2},
        )
        assert resp.status_code in (409, 422)
        body = resp.json()
        assert body["success"] is False
        assert "该用户名已被注册" in body["error"]["message"]


# ─── TC-004: Password mismatch ─────────────────────────────────────────────────

class TestPasswordMismatch:
    """TC-004: Password != confirm_password returns validation error."""

    async def test_register_password_mismatch_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_mismatch",
                "password": "Pass@123",
                "confirm_password": "Pass@456",
                "email": "mismatch@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert "两次输入的密码不一致" in body["error"]["message"]


# ─── TC-005: Password strength boundary values ─────────────────────────────────

class TestPasswordStrength:
    """TC-005: Password length <8 or >32 returns validation error."""

    async def test_register_password_7_chars_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_pw7",
                "password": "Ab1!xYz",
                "confirm_password": "Ab1!xYz",
                "email": "pw7@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422

    async def test_register_password_8_chars_succeeds(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_pw8",
                "password": "Ab1!xYz9",
                "confirm_password": "Ab1!xYz9",
                "email": "pw8@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_register_password_32_chars_succeeds(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        pw32 = "aB1!cD2@eF3#gH4$iJ5%kL6^mN7&oP8*"
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_pw32",
                "password": pw32,
                "confirm_password": pw32,
                "email": "pw32@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_register_password_33_chars_returns_422(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        pw33 = "aB1!cD2@eF3#gH4$iJ5%kL6^mN7&oP8*q"
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_pw33",
                "password": pw33,
                "confirm_password": pw33,
                "email": "pw33@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 422


# ─── TC-006: Valid registration → account created → auto-login → JWT Cookie ───

class TestValidRegistration:
    """TC-006: Valid registration creates account, auto-login, JWT cookie, redirect."""

    async def test_register_valid_credentials_creates_account_and_returns_jwt_cookie(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_valid",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "valid@leecloud.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user"]["username"] == "testuser_valid"
        assert body["data"]["redirect"] == "/console"

    async def test_register_sets_httpOnly_secure_samesite_cookie(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_cookie",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "cookie@leecloud.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200

        set_cookie_headers = resp.headers.get_list("set-cookie")
        jwt_cookie = None
        for hdr in set_cookie_headers:
            if "jwt_token" in hdr:
                jwt_cookie = hdr
                break
        assert jwt_cookie is not None
        assert "HttpOnly" in jwt_cookie
        assert "Secure" in jwt_cookie
        assert "SameSite" in jwt_cookie

    async def test_register_jwt_cookie_contains_valid_token(self, async_client):
        import jwt
        from conftest import JWT_SECRET, JWT_ALGORITHM

        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser_jwt",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "jwt@leecloud.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200
        raw_cookie = resp.cookies.get("jwt_token")
        assert raw_cookie is not None
        decoded = jwt.decode(raw_cookie, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "sub" in decoded
        assert "username" in decoded
        assert "exp" in decoded


# ─── TC-007: Register page link to /auth/login ─────────────────────────────────

class TestRegisterToLoginLink:
    """TC-007: Register page has link to /auth/login."""

    async def test_register_page_contains_login_link(self, async_client):
        resp = await async_client.get("/auth/register")
        assert resp.status_code == 200
        assert "/auth/login" in resp.text
        assert "已有账户？返回登录" in resp.text


# ─── TC-008: Authenticated user accessing /auth/register → redirect to /console

class TestAuthenticatedUserRedirect:
    """TC-008: Authenticated user accessing /auth/register is redirected to /console."""

    async def test_authenticated_user_redirected_from_register(self, async_client):
        import jwt as pyjwt
        from datetime import datetime, timezone, timedelta

        now = int(datetime.now(timezone.utc).timestamp())
        access = pyjwt.encode(
            {"jti": "test-jti-008", "sub": "user-008", "username": "authuser",
             "role": "user", "iat": now, "exp": now + 86400},
            "test-secret-key", algorithm="HS256",
        )
        resp = await async_client.get(
            "/auth/register",
            cookies={"jwt_token": access},
        )
        assert resp.status_code in (302, 307, 303)
        location = resp.headers.get("location", "")
        assert "/console" in location


# ─── EC-003: XSS/SQL injection input sanitization ─────────────────────────────

class TestXSSAndSQLInjection:
    """EC-003: XSS/SQL injection — server sanitizes or rejects malicious input."""

    async def test_register_xss_script_tags_in_username_rejected(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "<script>alert('xss')</script>",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "xss@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code in (422, 400)
        body = resp.json()
        assert body["success"] is False

    async def test_register_sql_injection_in_username_rejected(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin'; DROP TABLE users; --",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "sqli@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code in (422, 400)
        body = resp.json()
        assert body["success"] is False

    async def test_register_sql_keywords_in_username_rejected(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "1 OR 1=1",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "sqli2@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code in (422, 400)


# ─── EC-004: CSRF protection on register endpoint ──────────────────────────────

class TestCSRFProtection:
    """EC-004 / FR-020: CSRF protection on register endpoint."""

    async def test_register_without_csrf_returns_403(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "csrf_test_user",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "csrf@example.com",
            },
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["success"] is False
        assert "CSRF" in body["error"]["message"] or "csrf" in body["error"]["message"].lower()

    async def test_register_with_invalid_csrf_returns_403(self, async_client):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "csrf_test_user2",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "csrf2@example.com",
            },
            headers={"x-csrf-token": "invalid-csrf-token-value"},
            cookies={"csrf_token": "some-other-csrf"},
        )
        assert resp.status_code == 403

    async def test_register_with_valid_csrf_succeeds(self, async_client):
        csrf_resp = await async_client.get("/api/v1/auth/csrf")
        csrf_token = csrf_resp.json()["data"]["csrf_token"]
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "csrf_valid_user",
                "password": "Pass@123",
                "confirm_password": "Pass@123",
                "email": "csrfvalid@example.com",
            },
            headers={"x-csrf-token": csrf_token},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
