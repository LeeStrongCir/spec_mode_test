"""特性级 fixtures for 001-register-login 集成测试"""

import pytest


@pytest.fixture
def csrf_api_client(api_client):
    """携带 CSRF Token 的认证客户端"""

    async def get_with_csrf(path):
        response = await api_client.get(path)
        import re
        match = re.search(r'<input[^>]*name="_csrf_token"[^>]*value="([^"]+)"', response.text)
        csrf_token = match.group(1) if match else None
        return response, csrf_token

    api_client.get_with_csrf = get_with_csrf
    yield api_client
