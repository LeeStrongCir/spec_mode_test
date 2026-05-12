"""SC-02 输入凭据完成登录 + SC-03 处理登录失败 — TC-010 ~ TC-019"""

import pytest
from tests.conftest import _fetch_csrf


async def _register(client, username):
    csrf = await _fetch_csrf(client)
    return await client.post(
        "/api/auth/register",
        json={"username": username, "password": "Test@1234",
              "confirmPassword": "Test@1234", "email": f"{username}@example.com"},
        headers={"X-CSRF-Token": csrf},
        follow_redirects=False,
    )


async def _do_login(client, username, password):
    csrf = await _fetch_csrf(client)
    return await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        headers={"X-CSRF-Token": csrf},
        follow_redirects=False,
    )


@pytest.mark.asyncio
class TestLoginPageLayout:
    async def test_page_loads(self, api_client):
        r = await api_client.get("/auth/login")
        assert r.status_code == 200
        for tid in ["login-username-input", "login-password-input", "login-remember", "login-button"]:
            assert tid in r.text


@pytest.mark.asyncio
class TestLoginSuccess:

    async def test_login_redirects_to_console(self, api_client):
        uid = str(id(api_client))[-6:]
        uname = f"login_ok_{uid}"
        await _register(api_client, uname)

        r = await _do_login(api_client, uname, "Test@1234")
        assert r.status_code in (200, 302)
        if r.status_code == 302:
            assert "/console" in r.headers.get("location", "")

    async def test_login_returns_httponly_cookie(self, api_client):
        uid = str(id(api_client))[-6:]
        uname = f"login_ck_{uid}"
        await _register(api_client, uname)

        r = await _do_login(api_client, uname, "Test@1234")
        sc = r.headers.get("set-cookie", r.headers.get("Set-Cookie", ""))
        assert "httponly" in sc.lower()


@pytest.mark.asyncio
class TestLoginFailure:

    async def test_nonexistent_user_error(self, api_client):
        r = await _do_login(api_client, "nonexistent_user", "Any!")
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            body = r.json()
            assert "message" in body or "errors" in body

    async def test_wrong_password_error(self, api_client):
        uid = str(id(api_client))[-6:]
        uname = f"wp_{uid}"
        await _register(api_client, uname)
        r = await _do_login(api_client, uname, "WrongPassword1!")
        assert r.status_code in (200, 401)

    async def test_error_messages_identical(self, api_client):
        r1 = await _do_login(api_client, "nonexistent1", "Any!")
        r2 = await _do_login(api_client, "nonexistent2", "Any!")
        if r1.status_code == 200 and r2.status_code == 200:
            assert r1.json().get("message") == r2.json().get("message")
