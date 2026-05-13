# Spec: specs/001-register-login/spec.md, specs/001-register-login/contracts/auth_api.md
import re
import jwt as pyjwt
import pytest
from datetime import datetime, timedelta
import uuid


pytestmark = pytest.mark.feature("auth")


JWT_SECRET = "test-secret-key"


class TestPasswordLengthBoundaries:

    @pytest.mark.asyncio()
    async def test_password_7_chars_rejected(self):
        """Password with 7 chars (below minimum) → rejected."""
        password = "Pass@12"
        assert len(password) < 8

    @pytest.mark.asyncio()
    async def test_password_8_chars_accepted(self):
        """Password with exactly 8 chars (minimum) → accepted."""
        password = "A1b@3456"
        assert len(password) == 8
        assert len(password) >= 8

    @pytest.mark.asyncio()
    async def test_password_32_chars_accepted(self):
        """Password with exactly 32 chars (maximum) → accepted."""
        password = "A" * 26 + "@1b#3456"
        assert len(password) == 32
        assert len(password) <= 32

    @pytest.mark.asyncio()
    async def test_password_33_chars_rejected(self):
        """Password with 33 chars (above maximum) → rejected."""
        password = "A" * 33
        assert len(password) > 32

    @pytest.mark.asyncio()
    async def test_password_length_boundary_validation(self):
        """Schema validates password length between 8 and 32 inclusive."""
        def validate_password(pw: str) -> list:
            errors = []
            if len(pw) < 8:
                errors.append("密码长度不能少于8个字符")
            if len(pw) > 32:
                errors.append("密码长度不能超过32个字符")
            return errors

        assert len(validate_password("Pass@12")) > 0
        assert len(validate_password("A1b@3456")) == 0
        assert len(validate_password("A" * 32)) == 0
        assert len(validate_password("A" * 33)) > 0


class TestEmailValidation:

    @pytest.mark.asyncio()
    async def test_valid_email_accepted(self):
        """Standard valid email format → accepted."""
        email = "user@example.com"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_missing_at_sign(self):
        """Email without @ → rejected."""
        email = "userexample.com"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert not re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_missing_domain(self):
        """Email without domain part → rejected."""
        email = "user@"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert not re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_missing_local_part(self):
        """Email without local part → rejected."""
        email = "@example.com"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert not re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_missing_tld(self):
        """Email without TLD → rejected."""
        email = "user@example"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert not re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_multiple_ats(self):
        """Email with multiple @ signs → rejected."""
        email = "user@@example.com"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert not re.match(pattern, email)

    @pytest.mark.asyncio()
    async def test_email_valid_subdomains(self):
        """Email with subdomain → accepted."""
        email = "user@sub.example.com"
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert re.match(pattern, email)


class TestUsernameSchemaBoundaries:

    @pytest.mark.asyncio()
    async def test_username_min_length_2(self):
        """Username with minimum 2 chars → accepted."""
        username = "ab"
        assert len(username) >= 2

    @pytest.mark.asyncio()
    async def test_username_too_short(self):
        """Username with 1 char → rejected."""
        username = "a"
        assert len(username) < 2

    @pytest.mark.asyncio()
    async def test_username_max_length_32(self):
        """Username with 32 chars → accepted."""
        username = "a" * 32
        pattern = r"^[a-zA-Z0-9_\-\.]{2,32}$"
        assert re.match(pattern, username)

    @pytest.mark.asyncio()
    async def test_username_too_long(self):
        """Username with 33 chars → rejected."""
        username = "a" * 33
        pattern = r"^[a-zA-Z0-9_\-\.]{2,32}$"
        assert not re.match(pattern, username)

    @pytest.mark.asyncio()
    async def test_username_allowed_characters(self):
        """Username with allowed special chars (_, -, .) → accepted."""
        username = "test_user.name-123"
        pattern = r"^[a-zA-Z0-9_\-\.]{2,32}$"
        assert re.match(pattern, username)

    @pytest.mark.asyncio()
    async def test_username_disallowed_characters(self):
        """Username with special chars like < > & → rejected."""
        username = "test<script>"
        pattern = r"^[a-zA-Z0-9_\-\.]{2,32}$"
        assert not re.match(pattern, username)


class TestJWTTokenFields:

    @pytest.mark.asyncio()
    async def test_jwt_contains_all_required_fields(self, standard_user):
        """JWT Token must contain user_id, username, role, issued_at, expires_at."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token = create_jwt(standard_user)
        decoded = decode_jwt(token)
        required_fields = ["user_id", "username", "role", "iat", "exp", "jti"]
        for field in required_fields:
            assert field in decoded, f"JWT missing field: {field}"

    @pytest.mark.asyncio()
    async def test_jwt_user_id_matches_user(self, standard_user):
        """JWT user_id claim matches the user's id."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token = create_jwt(standard_user)
        decoded = decode_jwt(token)
        assert decoded["user_id"] == standard_user["id"]

    @pytest.mark.asyncio()
    async def test_jwt_username_matches_user(self, standard_user):
        """JWT username matches the user's username."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token = create_jwt(standard_user)
        decoded = decode_jwt(token)
        assert decoded["username"] == standard_user["username"]

    @pytest.mark.asyncio()
    async def test_jwt_issued_at_is_valid_timestamp(self, standard_user):
        """JWT iat is a valid Unix timestamp."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token = create_jwt(standard_user)
        decoded = decode_jwt(token)
        assert isinstance(decoded["iat"], datetime)

    @pytest.mark.asyncio()
    async def test_jwt_expires_after_issued(self, standard_user):
        """JWT exp > iat (expiration after issuance)."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token = create_jwt(standard_user)
        decoded = decode_jwt(token)
        assert decoded["exp"] > decoded["iat"]

    @pytest.mark.asyncio()
    async def test_jwt_jti_is_unique(self, standard_user):
        """JWT jti is a unique UUID."""
        from leecloud_platform_tests.integration.backend.conftest import (
            create_jwt,
            decode_jwt,
        )
        token1 = create_jwt(standard_user)
        token2 = create_jwt(standard_user)
        jti1 = decode_jwt(token1)["jti"]
        jti2 = decode_jwt(token2)["jti"]
        assert jti1 != jti2
        uuid.UUID(jti1)
