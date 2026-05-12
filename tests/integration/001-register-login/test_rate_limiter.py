"""SC-05 速率限制器 — EC-002"""

import pytest
from tests.conftest import _fetch_csrf


@pytest.mark.asyncio
class TestIPRateLimiting:

    async def test_exceeds_rate_limit(self, api_client):
        csrf = await _fetch_csrf(api_client)
        ip = "192.168.1.200"
        status_codes = []
        for i in range(12):
            r = await api_client.post(
                "/api/auth/login",
                json={"username": "ratelimit_user", "password": "wrong"},
                headers={"X-CSRF-Token": csrf, "X-Forwarded-For": ip},
                follow_redirects=False,
            )
            status_codes.append(r.status_code)
        assert 429 in status_codes, f"No 429 received. Got: {set(status_codes)}"
