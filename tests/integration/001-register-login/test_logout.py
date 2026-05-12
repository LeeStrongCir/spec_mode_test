"""SC-04 退出登录 — TC-020"""

import pytest
from tests.conftest import _fetch_csrf


async def _register(client, username):
    csrf = await _fetch_csrf(client)
    return await client.post(
        "/api/auth/register",
        json={"username": username, "password": "Test@1234",
              "confirm_password": "Test@1234", "email": f"{username}@example.com"},
        headers={"X-CSRF-Token": csrf},
        follow_redirects=False,
    )


@pytest.mark.asyncio
class TestLogoutFlow:

    async def test_logout_redirects_to_login(self, api_client):
        uid = str(id(api_client))[-6:]
        uname = f"logout_{uid}"
        await _register(api_client, uname)

        csrf = await _fetch_csrf(api_client)
        r = await api_client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": csrf},
            follow_redirects=False,
        )
        assert r.status_code in (200, 302)
        if r.status_code == 302:
            assert "/auth/login" in r.headers.get("location", "")
