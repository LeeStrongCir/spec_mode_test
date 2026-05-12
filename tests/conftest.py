"""
Global conftest for 001-register-login tests.
Tests communicate with the running app at http://localhost:3000 via HTTP.
"""

import pytest
import fakeredis
from httpx import AsyncClient


@pytest.fixture
def redis_client():
    return fakeredis.FakeStrictRedis()


@pytest.fixture
async def api_client():
    async with AsyncClient(
        base_url="http://localhost:3000",
        follow_redirects=False,
        timeout=10.0
    ) as client:
        client.audit_log = []
        yield client


@pytest.fixture
async def authenticated_client(api_client):
    csrf = await _fetch_csrf(api_client)
    username = f"auth_test_{hash(api_client)}"
    await api_client.post(
        "/api/auth/register",
        data={
            "username": username,
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": f"{username}@example.com",
            "_csrf_token": csrf,
        },
        follow_redirects=False,
    )
    await api_client.post("/api/auth/logout", follow_redirects=False)
    yield api_client
    # cleanup: logout
    await api_client.post("/api/auth/logout", follow_redirects=False)


async def _fetch_csrf(client: AsyncClient) -> str | None:
    r = await client.get("/api/auth/csrf")
    if r.status_code == 200:
        return r.json().get("csrfToken")
    return None
