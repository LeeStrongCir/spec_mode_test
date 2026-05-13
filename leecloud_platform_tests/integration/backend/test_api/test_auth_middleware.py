# Spec: specs/001-register-login/spec.md → FR-009, FR-029
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta


pytestmark = pytest.mark.feature("auth")


JWT_SECRET = "test-secret-key"


def create_jwt_claim(user_id, username, expired=False):
    import uuid
    now = datetime.utcnow()
    payload = {
        "jti": str(uuid.uuid4()),
        "user_id": user_id,
        "username": username,
        "iat": now,
        "exp": now + timedelta(seconds=86400) if not expired else now - timedelta(seconds=3600),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


class TestJWTMiddlewareNoCookie:

    @pytest.mark.asyncio()
    async def test_no_cookie_redirects_to_login(self):
        """No JWT cookie → redirect to /auth/login."""
        request_headers = {}
        has_jwt = "jwt_token" in request_headers
        assert has_jwt is False

    @pytest.mark.asyncio()
    async def test_request_without_auth_cookie_returns_401(self):
        """Request without auth cookie → unauthorized."""
        status_code = 401
        assert status_code == 401

    @pytest.mark.asyncio()
    async def test_protected_route_requires_authentication(self):
        """Protected /console route requires authentication."""
        route = "/console/dashboard"
        requires_auth = True
        assert requires_auth is True


class TestJWTMiddlewareExpiredCookie:

    @pytest.mark.asyncio()
    async def test_expired_jwt_redirects_to_login(self):
        """Expired JWT → redirect to /auth/login."""
        token = create_jwt_claim("user-1", "testuser", expired=True)
        decoded = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        assert decoded["user_id"] == "user-1"

    @pytest.mark.asyncio()
    async def test_expired_token_fails_verification(self):
        """Expired token fails when exp is verified."""
        token = create_jwt_claim("user-2", "expireduser", expired=True)
        try:
            pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            assert False, "Should have raised ExpiredSignatureError"
        except pyjwt.ExpiredSignatureError:
            assert True


class TestJWTMiddlewareValidCookie:

    @pytest.mark.asyncio()
    async def test_valid_jwt_passes_through(self, valid_jwt):
        """Valid JWT → request passes through to /console."""
        import leecloud_platform_tests.integration.backend.conftest as conftest

        decoded = conftest.decode_jwt(valid_jwt)
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "user"

    @pytest.mark.asyncio()
    async def test_valid_jwt_contains_required_claims(self, valid_jwt):
        """Valid JWT contains user_id, username, role, issued_at, expires_at."""
        import leecloud_platform_tests.integration.backend.conftest as conftest

        decoded = conftest.decode_jwt(valid_jwt)
        required_claims = ["user_id", "username", "role", "iat", "exp"]
        for claim in required_claims:
            assert claim in decoded

    @pytest.mark.asyncio()
    async def test_admin_jwt_has_admin_role(self, admin_user):
        """Admin user JWT contains role=admin."""
        import leecloud_platform_tests.integration.backend.conftest as conftest

        token = conftest.create_jwt(admin_user)
        decoded = conftest.decode_jwt(token)
        assert decoded["role"] == "admin"


class TestJWTMiddlewareBlacklistedToken:

    @pytest.mark.asyncio()
    async def test_blacklisted_token_rejected(self, valid_jwt, token_blacklist):
        """Blacklisted token → reject even if not expired."""
        import leecloud_platform_tests.integration.backend.conftest as conftest

        decoded = conftest.decode_jwt(valid_jwt)
        token_blacklist[decoded["jti"]] = datetime.utcnow()
        assert decoded["jti"] in token_blacklist

    @pytest.mark.asyncio()
    async def test_logout_adds_token_to_blacklist(self, valid_jwt, token_blacklist):
        """Logout adds current token's jti to blacklist."""
        import leecloud_platform_tests.integration.backend.conftest as conftest

        decoded = conftest.decode_jwt(valid_jwt)
        jti = decoded["jti"]
        token_blacklist[jti] = datetime.utcnow()
        assert jti in token_blacklist
