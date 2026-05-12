"""SC-01 注册新账户 集成测试 — TC-001 ~ TC-009"""

import pytest
from tests.conftest import _fetch_csrf


@pytest.mark.asyncio
class TestRegisterPageLayout:

    async def test_page_loads(self, api_client):
        r = await api_client.get("/auth/register")
        assert r.status_code == 200
        for tid in ["register-username-input", "register-password-input",
                     "register-confirm-password-input", "register-email-input",
                     "register-button", "register-login-link"]:
            assert tid in r.text


@pytest.mark.asyncio
class TestRegisterEmptyValidation:

    async def test_empty_form_submit(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "", "password": "", "confirmPassword": "", "email": ""},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422
        body = r.json()
        assert "errors" in body

    async def test_partial_fill_errors(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "Test@1234"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422
        body = r.json()
        assert "errors" in body


@pytest.mark.asyncio
class TestRegisterUsernameUniqueness:

    async def test_duplicate_username_rejected(self, api_client):
        import random
        username = f"dup_{random.randint(10000,99999)}"
        csrf = await _fetch_csrf(api_client)
        r1 = await api_client.post("/api/auth/register",
            json={"username": username, "password": "Test@1234",
                  "confirmPassword": "Test@1234", "email": f"{username}@example.com"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r1.status_code == 200 and r1.json().get("success") is True

        csrf2 = await _fetch_csrf(api_client)
        r2 = await api_client.post("/api/auth/register",
            json={"username": username, "password": "Another@123",
                  "confirmPassword": "Another@123", "email": f"dup_{random.randint(10000,99999)}@example.com"},
            headers={"X-CSRF-Token": csrf2},
            follow_redirects=False,
        )
        assert r2.status_code in (200, 409) and r2.json().get("success") is not True


@pytest.mark.asyncio
class TestRegisterPasswordConsistency:

    async def test_password_mismatch_rejected(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "mismatch", "password": "Abcdefg1!",
                  "confirmPassword": "Different123!", "email": "mismatch@example.com"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422 and r.json().get("success") is not True


@pytest.mark.asyncio
class TestRegisterPasswordStrength:

    async def test_password_too_short(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "short", "password": "Ab1!", "confirmPassword": "Ab1!", "email": "s@example.com"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422 and r.json().get("success") is not True

    async def test_password_invalid_format(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "simple", "password": "abcdefgh", "confirmPassword": "abcdefgh", "email": "simple@example.com"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422 and r.json().get("success") is not True


@pytest.mark.asyncio
class TestRegisterEmailValidation:

    async def test_invalid_email_rejected(self, api_client):
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "bademail", "password": "Test@1234", "confirmPassword": "Test@1234", "email": "not-an-email"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 422 and r.json().get("success") is not True


@pytest.mark.asyncio
class TestRegisterSuccessFlow:

    async def test_register_succeeds(self, api_client):
        uid = str(id(api_client))[-6:]
        username = f"ok_{uid}"
        csrf = await _fetch_csrf(api_client)
        r = await api_client.post("/api/auth/register",
            json={"username": username, "password": "Test@1234",
                  "confirmPassword": "Test@1234", "email": f"{username}@example.com"},
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
