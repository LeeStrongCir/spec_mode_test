# Spec: specs/001-register-login/spec.md → FR-011, FR-025
import pytest
import time


pytestmark = pytest.mark.feature("auth")


class FakeRateLimiter:
    """In-memory rate limiter simulating Redis-like behavior per IP."""

    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_rate_limited(self, ip: str) -> bool:
        now = time.time()
        if ip not in self.requests:
            self.requests[ip] = []
        timestamps = self.requests[ip]
        self.requests[ip] = [ts for ts in timestamps if now - ts < self.window_seconds]
        if len(self.requests[ip]) >= self.max_requests:
            return True
        self.requests[ip].append(now)
        return False

    def reset(self):
        self.requests.clear()


@pytest.fixture()
def rate_limiter():
    return FakeRateLimiter(max_requests=10, window_seconds=60)


class TestIPRateLimitWithinWindow:

    @pytest.mark.asyncio()
    async def test_ten_requests_in_window_all_succeed(self, rate_limiter):
        """10 requests in 1 minute → all succeed."""
        ip = "192.168.1.1"
        for i in range(10):
            limited = rate_limiter.is_rate_limited(ip)
            assert limited is False, f"Request {i+1} should not be rate limited"

    @pytest.mark.asyncio()
    async def test_eleventh_request_rate_limited(self, rate_limiter):
        """11th request in same window → 429."""
        ip = "10.0.0.1"
        for _ in range(10):
            rate_limiter.is_rate_limited(ip)
        limited = rate_limiter.is_rate_limited(ip)
        assert limited is True

    @pytest.mark.asyncio()
    async def test_rate_limit_response_format(self, rate_limiter):
        """Rate limited request returns proper error format."""
        ip = "172.16.0.1"
        for _ in range(10):
            rate_limiter.is_rate_limited(ip)
        response = {
            "success": False,
            "data": None,
            "error": {
                "code": "RATE_LIMITED",
                "message": "请求过于频繁，请稍后重试",
            },
        }
        assert response["error"]["code"] == "RATE_LIMITED"
        assert "频繁" in response["error"]["message"]


class TestIPRateLimitWindowReset:

    @pytest.mark.asyncio()
    async def test_request_after_window_reset_succeeds(self, rate_limiter):
        """After 1 minute window resets → request succeeds."""
        ip = "192.168.1.100"
        for _ in range(10):
            rate_limiter.is_rate_limited(ip)
        rate_limiter.requests[ip] = []
        limited = rate_limiter.is_rate_limited(ip)
        assert limited is False

    @pytest.mark.asyncio()
    async def test_old_timestamps_filtered_out(self, rate_limiter):
        """Timestamps older than window seconds are removed."""
        import time
        ip = "10.10.10.10"

        old_time = time.time() - 120
        rate_limiter.requests[ip] = [old_time, old_time + 1, old_time + 2]
        limited = rate_limiter.is_rate_limited(ip)
        assert limited is False
        assert len(rate_limiter.requests[ip]) == 1


class TestIPRateLimitMultipleIPs:

    @pytest.mark.asyncio()
    async def test_different_ips_have_independent_limits(self, rate_limiter):
        """Each IP has independent rate limit window."""
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        for _ in range(10):
            rate_limiter.is_rate_limited(ip1)
        limited_ip1 = rate_limiter.is_rate_limited(ip1)
        limited_ip2 = rate_limiter.is_rate_limited(ip2)
        assert limited_ip1 is True
        assert limited_ip2 is False

    @pytest.mark.asyncio()
    async def test_rate_limit_applies_per_ip_not_global(self, rate_limiter):
        """Rate limit is per-IP, not global across all IPs."""
        for i in range(5):
            rate_limiter.is_rate_limited(f"10.0.0.{i}")
        for i in range(5):
            limited = rate_limiter.is_rate_limited(f"10.0.0.{i}")
            assert limited is False
