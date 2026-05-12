"""特性级 fixtures for 002-lecs-host 集成测试"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta


# ─── User Data Models ──────────────────────────────────

class UserData:
    """Minimal user data holder for test fixtures."""
    def __init__(self, user_id: str, username: str, role: str = "user"):
        self.id = user_id
        self.username = username
        self.role = role


# ─── JWT Helpers ───────────────────────────────────────

TEST_JWT_SECRET = "test-secret-key-for-testing-only"


def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def create_jwt_token(user_id: str, username: str = "test_user", role: str = "user",
                     exp_offset_seconds: int = 3600, issued_at: datetime | None = None):
    """Create a simple JWT-like token for testing (header.payload.signature).

    The payload is signed with a predictable test secret to allow tamper detection.
    For testing expired tokens, use a negative exp_offset_seconds.
    """
    import json
    import hmac
    import hashlib

    header = {"alg": "HS256", "typ": "JWT"}
    now = issued_at or datetime.utcnow()
    exp = now + timedelta(seconds=exp_offset_seconds)

    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    header_b64 = _base64url_encode(json.dumps(header).encode())
    payload_b64 = _base64url_encode(json.dumps(payload).encode())
    message = f"{header_b64}.{payload_b64}"
    signature = _base64url_encode(
        hmac.new(TEST_JWT_SECRET.encode(), message.encode(), hashlib.sha256).digest()
    )
    return f"{message}.{signature}"


def create_service_token(service_name: str = "lecs-test"):
    """Create a mock service token for non-browser API authentication."""
    import json
    return f"svc_{service_name}_{uuid4().hex}"


# ─── Pytest Fixtures: Users ────────────────────────────

@pytest.fixture
def test_user():
    """普通用户 (normal user, role='user')."""
    return UserData(user_id="user-a-001", username="user_a", role="user")


@pytest.fixture
def other_user():
    """另一个普通用户 (用于越权测试)."""
    return UserData(user_id="user-b-002", username="user_b", role="user")


@pytest.fixture
def admin_user():
    """管理员用户 (role='admin')."""
    return UserData(user_id="admin-001", username="admin_user", role="admin")


# ─── Pytest Fixtures: Authenticated Clients ────────────

@pytest.fixture
def jwt_authenticated_client(api_client, test_user):
    """已认证的客户端，携带有效 JWT Cookie（普通用户）."""
    token = create_jwt_token(test_user.id, test_user.username, test_user.role)
    api_client.cookies.set("lecs_jwt", token)
    yield api_client


@pytest.fixture
def admin_authenticated_client(api_client, admin_user):
    """已认证的管理员客户端，携带有效 JWT Cookie."""
    token = create_jwt_token(admin_user.id, admin_user.username, admin_user.role)
    api_client.cookies.set("lecs_jwt", token)
    yield api_client


@pytest.fixture
def expired_jwt_client(api_client, test_user):
    """携带过期 JWT Cookie 的客户端."""
    token = create_jwt_token(test_user.id, test_user.username, test_user.role,
                             exp_offset_seconds=-3600)
    api_client.cookies.set("lecs_jwt", token)
    yield api_client


@pytest.fixture
def service_token_client(api_client):
    """携带 Service Token 的客户端（用于非浏览器 API 调用）."""
    token = create_service_token()
    api_client.headers["Authorization"] = f"Bearer {token}"
    yield api_client


@pytest.fixture
def invalid_jwt_client(api_client):
    """携带伪造 JWT Cookie 的客户端."""
    api_client.cookies.set("lecs_jwt", "invalid_random_garbage_token")
    yield api_client


# ─── Host Data Helpers ─────────────────────────────────

HOST_BASE_URL = "http://localhost:3000"
API_PREFIX = "/api/v1/lecs-hosts"


def make_valid_create_payload(user_id: str | None = None) -> dict:
    """Generate a valid host creation request body."""
    uid = user_id or str(uuid4())
    return {
        "billing_mode": "包年/包月",
        "host_name": f"test_host_{uid[:8]}",
        "username": "valid_user",
        "password": "Abcdef12!",
        "instance_type": "经济型",
        "instance_spec": "eco-001",
        "os_image": "Ubuntu 22.04 LTS",
        "ip_config": {
            "mode": "DHCP",
        },
        "duration": 1,
    }


# ─── Async Queue Mock ──────────────────────────────────

class MockAsyncResult:
    """mock Celery AsyncResult"""
    id: str = str(uuid4())

    def __init__(self, task_id=None):
        if task_id:
            self.id = task_id


@pytest.fixture
def mock_async_queue():
    """mock 异步任务队列，记录任务提交但不实际执行

    验证方式:
        mock_async_queue.assert_called_once()
        mock_async_queue.call_args
    """
    mock = MagicMock(return_value=MockAsyncResult())
    with patch("celery.Celery.send_task", mock):
        yield mock


# ─── Billing Service Mock ──────────────────────────────

FIXED_RATES = {
    "eco-001": {"monthly_price_cents": 10000, "vcpu": 2, "memory_gib": 2, "name": "通用计算机"},
    "eco-002": {"monthly_price_cents": 14000, "vcpu": 2, "memory_gib": 4, "name": "通用计算机"},
    "eco-003": {"monthly_price_cents": 18000, "vcpu": 2, "memory_gib": 8, "name": "通用计算机"},
    "eco-004": {"monthly_price_cents": 24000, "vcpu": 4, "memory_gib": 8, "name": "通用计算机"},
    "hp-001": {"monthly_price_cents": 16000, "vcpu": 2, "memory_gib": 4, "name": "通用增强计算机"},
    "hp-002": {"monthly_price_cents": 20000, "vcpu": 2, "memory_gib": 8, "name": "通用增强计算机"},
    "hp-003": {"monthly_price_cents": 26000, "vcpu": 4, "memory_gib": 8, "name": "通用增强计算机"},
    "hp-004": {"monthly_price_cents": 50000, "vcpu": 8, "memory_gib": 16, "name": "通用增强计算机"},
}


@pytest.fixture
def mock_billing_service():
    """mock 计费服务，返回固定费率表"""
    with patch("app.services.billing.get_rates", return_value=FIXED_RATES) as mock:
        yield mock


# ─── State Machine Helpers ──────────────────────────────

VALID_TRANSITIONS = {
    "normal": {"stop": "shutting_down"},
    "stopped": {"start": "starting", "delete": "deleting"},
    "failed": {"start": "starting", "delete": "deleting"},
    "creating": {},
    "shutting_down": {},
    "starting": {},
    "deleting": {},
}


def assert_transition_blocked(response, action, current_state):
    """断言状态转换被正确拦截"""
    assert response.status_code in (403, 409), (
        f"Action '{action}' on state '{current_state}' should be blocked, got {response.status_code}"
    )
