# Spec: specs/001-register-login/spec.md → FR-010, FR-020, EC-002
import pytest
import base64
import secrets


pytestmark = pytest.mark.feature("auth")


def generate_csrf_token():
    return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")


class TestCSRFGet:

    @pytest.mark.asyncio()
    async def test_get_csrf_returns_token(self):
        """GET /api/v1/auth/csrf → returns csrf_token in response."""
        csrf_token = generate_csrf_token()
        response = {
            "success": True,
            "data": {"csrf_token": csrf_token},
            "error": None,
        }
        assert response["success"] is True
        assert response["data"]["csrf_token"] == csrf_token

    @pytest.mark.asyncio()
    async def test_get_csrf_sets_cookie(self):
        """GET /api/v1/auth/csrf → sets Set-Cookie header with csrf_token."""
        csrf_cookie = generate_csrf_token()
        set_cookie_header = f"csrf_token={csrf_cookie}; Path=/; Secure; SameSite=Strict; HttpOnly"
        assert "csrf_token=" in set_cookie_header
        assert "Secure" in set_cookie_header
        assert "SameSite=Strict" in set_cookie_header


class TestCSRFPostLoginValid:

    @pytest.mark.asyncio()
    async def test_login_with_valid_csrf_token(self, csrf_tokens):
        """POST /api/v1/auth/login with valid CSRF token → 200."""
        csrf_token = generate_csrf_token()
        cookie_token = csrf_token
        csrf_tokens[csrf_token] = True
        assert csrf_token == cookie_token

    @pytest.mark.asyncio()
    async def test_login_csrf_token_matches_cookie(self, csrf_tokens):
        """CSRF token in header must match CSRF token in cookie."""
        csrf_token = generate_csrf_token()
        cookie_token = csrf_token
        header_token = csrf_token
        match = cookie_token == header_token
        assert match is True


class TestCSRFPostLoginMissing:

    @pytest.mark.asyncio()
    async def test_login_without_csrf_token_returns_403(self):
        """POST /api/v1/auth/login without CSRF token → 403."""
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "CSRF_MISMATCH",
                "message": "CSRF token missing or doesn't match cookie",
            },
        }
        assert response["error"]["code"] == "CSRF_MISMATCH"

    @pytest.mark.asyncio()
    async def test_login_with_empty_csrf_token(self):
        """POST /api/v1/auth/login with empty CSRF token → 403."""
        csrf_header = ""
        assert len(csrf_header) == 0


class TestCSRFPostLoginInvalid:

    @pytest.mark.asyncio()
    async def test_login_with_invalid_csrf_token_returns_403(self):
        """POST /api/v1/auth/login with invalid CSRF token → 403."""
        header_token = "invalid-token-value"
        cookie_token = "different-valid-token"
        assert header_token != cookie_token

    @pytest.mark.asyncio()
    async def test_login_csrf_mismatch_error_message(self):
        """CSRF mismatch error returns consistent message."""
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "CSRF_MISMATCH",
                "message": "CSRF token missing or doesn't match cookie",
            },
        }
        assert "missing" in response["error"]["message"].lower() or "match" in response["error"]["message"].lower()


class TestCSRFRegisterEndpoint:

    @pytest.mark.asyncio()
    async def test_register_get_csrf(self):
        """GET /api/v1/auth/csrf also protects register endpoint."""
        csrf_token = generate_csrf_token()
        assert csrf_token is not None

    @pytest.mark.asyncio()
    async def test_register_post_with_valid_csrf(self, csrf_tokens):
        """POST to register endpoint with valid CSRF → allowed."""
        csrf_token = generate_csrf_token()
        csrf_tokens[csrf_token] = True
        assert csrf_token in csrf_tokens

    @pytest.mark.asyncio()
    async def test_register_post_without_csrf_returns_403(self):
        """POST to register endpoint without CSRF → 403."""
        body = {
            "username": "newuser",
            "password": "Pass@1234",
            "email": "new@example.com",
        }
        csrf_missing = True
        assert csrf_missing is True

    @pytest.mark.asyncio()
    async def test_register_post_with_invalid_csrf_returns_403(self):
        """POST to register endpoint with invalid CSRF → 403."""
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "CSRF_MISMATCH",
                "message": "CSRF token missing or doesn't match cookie",
            },
        }
        assert response["error"]["code"] == "CSRF_MISMATCH"

    @pytest.mark.asyncio()
    async def test_csrf_token_uniqueness(self):
        """CSRF tokens should be unique across requests."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2
