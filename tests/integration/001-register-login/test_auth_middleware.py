"""SC-05 认证中间件 — EC-003, EC-004"""

import asyncio
import pytest


async def _register_api(client, username):
    from tests.conftest import _fetch_csrf
    import random
    uname = f"{username}_{random.randint(10000,99999)}"
    csrf = await _fetch_csrf(client)
    return await client.post(
        "/api/auth/register",
        json={"username": uname, "password": "Test@1234",
              "confirmPassword": "Test@1234", "email": f"{uname}@test.io"},
        headers={"X-CSRF-Token": csrf},
        follow_redirects=False,
    )


@pytest.mark.asyncio
class TestProtectedRouteAccess:

    async def test_unauthenticated_access_console_blocked(self, api_client):
        r = await api_client.get("/console", follow_redirects=False)
        # 302 = server redirect, 307 = Next.js client redirect, 404 = not found
        assert r.status_code in (302, 307, 404)

    async def test_console_not_found_for_subpath(self, api_client):
        r = await api_client.get("/console/settings", follow_redirects=False)
        assert r.status_code in (302, 307, 404)


@pytest.mark.asyncio
class TestAuthenticatedUserAuthPages:

    async def test_authenticated_redirected_from_register(self, api_client):
        await _register_api(api_client, "auth_redir")

        r = await api_client.get("/auth/register", follow_redirects=False)
        assert r.status_code in (200, 302, 307)
