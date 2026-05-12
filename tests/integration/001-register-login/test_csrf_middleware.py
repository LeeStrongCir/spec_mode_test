"""SC-05 CSRF 中间件 — EC-001"""

import pytest


@pytest.mark.asyncio
class TestCSRFValidation:

    async def test_missing_csrf_token_returns_403(self, api_client):
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "no_csrf", "password": "Test@1234",
                  "confirm_password": "Test@1234", "email": "no_csrf@example.com"},
            follow_redirects=False,
        )
        assert r.status_code == 403

    async def test_forged_csrf_returns_403(self, api_client):
        r = await api_client.post(
            "/api/auth/register",
            json={"username": "forge_csrf", "password": "Test@1234",
                  "confirm_password": "Test@1234", "email": "forge_csrf@example.com"},
            headers={"X-CSRF-Token": "forged_token_xyz"},
            follow_redirects=False,
        )
        assert r.status_code == 403

    async def test_valid_csrf_passes(self, api_client):
        """Get CSRF token via GET, verify token format."""
        r = await api_client.get("/api/auth/csrf")
        assert r.status_code == 200
        data = r.json()
        assert "csrfToken" in data
        assert len(data["csrfToken"]) == 64
