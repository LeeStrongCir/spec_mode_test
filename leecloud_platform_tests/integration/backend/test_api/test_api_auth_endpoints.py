# Spec: specs/001-register-login/spec.md → TC-040-TC-047, FR-022-FR-030
# Edge Cases: EC-005, EC-006
"""API-Only Authentication Endpoint Tests (SC-05)."""

import json
import uuid
import time
import bcrypt
import pytest
from datetime import datetime, timedelta

pytestmark = pytest.mark.feature("api-auth")


# ─── In-Memory App Simulation ───

class InMemoryAuthApp:
    """Simulates auth API endpoints per the API contract."""

    JWT_SECRET = "test-secret-key"
    JWT_ALGORITHM = "HS256"
    LOGIN_RATE_LIMIT_WINDOW = 60
    LOGIN_RATE_LIMIT_MAX = 10
    ACCOUNT_LOCK_FAILURES = 5
    ACCOUNT_LOCK_DURATION = 900  # 15 minutes
    TOKEN_EXPIRES_IN = 86400

    def __init__(
        self,
        users,
        login_attempts,
        account_lockouts,
        ip_rate_limits,
        token_blacklist,
        audit_log,
        current_time=None,
    ):
        self.users = users
        self.login_attempts = login_attempts
        self.account_lockouts = account_lockouts
        self.ip_rate_limits = ip_rate_limits
        self.token_blacklist = token_blacklist
        self.audit_log = audit_log
        self._current_time = current_time or time.time()
        self.refresh_tokens = {}

    @property
    def now(self):
        return self._current_time

    @now.setter
    def now(self, value):
        self._current_time = value

    def _generate_jwt(self, user):
        jti = str(uuid.uuid4())
        now = datetime.utcnow()
        payload = {
            "jti": jti,
            "user_id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "iat": now,
            "exp": now + timedelta(seconds=self.TOKEN_EXPIRES_IN),
        }
        access_token = f"eyJhbGciOiJIUzI1NiJ9.{json.dumps(payload, default=str)}.sim_signature"
        refresh_token = str(uuid.uuid4())
        self.refresh_tokens[refresh_token] = {
            "user_id": user["id"],
            "expires_at": self.now + self.TOKEN_EXPIRES_IN,
            "jti": jti,
        }
        return access_token, refresh_token

    def _verify_password(self, user, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        )

    def _check_account_locked(self, username):
        key = f"username:{username}"
        lockout = self.account_lockouts.get(key)
        if lockout and self.now < lockout["locked_until"]:
            return True
        if lockout and self.now >= lockout["locked_until"]:
            del self.account_lockouts[key]
            if key in self.login_attempts:
                self.login_attempts[key]["count"] = 0
        return False

    def _check_ip_rate_limit(self, ip):
        key = f"ip:{ip}"
        if key not in self.ip_rate_limits:
            self.ip_rate_limits[key] = {"timestamps": []}
        window_start = self.now - self.LOGIN_RATE_LIMIT_WINDOW
        self.ip_rate_limits[key]["timestamps"] = [
            ts for ts in self.ip_rate_limits[key]["timestamps"] if ts > window_start
        ]
        return len(self.ip_rate_limits[key]["timestamps"]) >= self.LOGIN_RATE_LIMIT_MAX

    def _record_ip_request(self, ip):
        key = f"ip:{ip}"
        if key not in self.ip_rate_limits:
            self.ip_rate_limits[key] = {"timestamps": []}
        self.ip_rate_limits[key]["timestamps"].append(self.now)

    def _record_login_attempt(self, username, ip):
        key = f"username:{username}"
        if key not in self.login_attempts:
            self.login_attempts[key] = {"count": 0, "last_attempt": 0}
        self.login_attempts[key]["count"] += 1
        self.login_attempts[key]["last_attempt"] = self.now

    def _log_audit(self, action, username, ip, result, details=""):
        self.audit_log.append({
            "action": action,
            "username": username,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip": ip,
            "result": result,
            "details": details,
        })

    def _error_response(self, code, message, status, details=None):
        body = {"success": False, "data": None, "error": {"code": code, "message": message}}
        if details:
            body["error"]["details"] = details
        return (body, status)

    def _success_response(self, data, status=200):
        return ({"success": True, "data": data, "error": None}, status)

    def post_login(self, request, ip="127.0.0.1"):
        username = request.get("username", "")
        password = request.get("password", "")

        if not username or not password:
            return (self._error_response("VALIDATION_ERROR", "Validation error details", 422,
                details=[{"field": "username" if not username else "password",
                          "message": "用户名格式不正确，允许的字符：字母、数字、_."
                          if not username else "密码不能为空"}]), {})

        if self._check_ip_rate_limit(ip):
            self._log_audit("login", username, ip, "rate_limited", "IP rate limit exceeded")
            self._record_ip_request(ip)
            return (self._error_response("RATE_LIMITED", "请求过于频繁，请稍后重试", 429), {})

        self._record_ip_request(ip)

        if self._check_account_locked(username):
            self._log_audit("login", username, ip, "locked", "Account is locked")
            return (self._error_response("ACCOUNT_LOCKED", "账号已被临时锁定，请 15 分钟后再试", 423), {})

        user = self.users.get(username)
        if not user:
            self._record_login_attempt(username, ip)
            fail_key = f"username:{username}"
            if fail_key not in self.login_attempts:
                self.login_attempts[fail_key] = {"count": 0, "last_attempt": 0}
            self.login_attempts[fail_key]["count"] += 1
            if self.login_attempts[fail_key]["count"] >= 5:
                self.account_lockouts[fail_key] = {"locked_until": self.now + self.ACCOUNT_LOCK_DURATION}
            self._log_audit("login", username, ip, "failure", "User not found")
            return (self._error_response("INVALID_CREDENTIALS", "用户名或密码错误", 401), {})

        if not self._verify_password(user, password):
            self._record_login_attempt(username, ip)
            fail_key = f"username:{username}"
            if fail_key not in self.login_attempts:
                self.login_attempts[fail_key] = {"count": 0, "last_attempt": 0}
            self.login_attempts[fail_key]["count"] += 1
            if self.login_attempts[fail_key]["count"] >= 5:
                self.account_lockouts[fail_key] = {"locked_until": self.now + self.ACCOUNT_LOCK_DURATION}
            self._log_audit("login", username, ip, "failure", "Invalid password")
            return (self._error_response("INVALID_CREDENTIALS", "用户名或密码错误", 401), {})

        fail_key = f"username:{username}"
        if fail_key in self.login_attempts:
            self.login_attempts[fail_key]["count"] = 0

        access_token, refresh_token = self._generate_jwt(user)
        self._log_audit("login", username, ip, "success", "Login successful")

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": self.TOKEN_EXPIRES_IN,
            "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
        }
        return (self._success_response(response_data, 200), {})

    def post_refresh(self, request):
        refresh_token = request.get("refresh_token", "")

        if not refresh_token:
            return self._error_response("VALIDATION_ERROR", "Validation error details", 422,
                details=[{"field": "refresh_token", "message": "刷新令牌不能为空"}])

        token_data = self.refresh_tokens.get(refresh_token)
        if not token_data:
            return self._error_response("INVALID_TOKEN", "刷新令牌已过期", 401)

        if self.now > token_data["expires_at"]:
            del self.refresh_tokens[refresh_token]
            return self._error_response("INVALID_TOKEN", "刷新令牌已过期", 401)

        user_id = token_data["user_id"]
        del self.refresh_tokens[refresh_token]

        user = next((u for u in self.users.values() if u["id"] == user_id), None)
        if not user:
            return self._error_response("INVALID_TOKEN", "刷新令牌已过期", 401)

        access_token, new_refresh_token = self._generate_jwt(user)
        return self._success_response({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": self.TOKEN_EXPIRES_IN,
        }, 200)

    def post_logout(self, token, audit_user="unknown", audit_ip="127.0.0.1"):
        if not token:
            return self._error_response("UNAUTHORIZED", "未授权", 401)

        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid token format")
            payload = json.loads(parts[1])
            jti = payload.get("jti")
            username = payload.get("username", audit_user)
        except (json.JSONDecodeError, IndexError, ValueError):
            return self._error_response("UNAUTHORIZED", "未授权", 401)

        if not jti:
            return self._error_response("UNAUTHORIZED", "未授权", 401)

        if jti in self.token_blacklist:
            self._log_audit("logout", username, audit_ip, "failure", "Token already blacklisted")
            return self._error_response("UNAUTHORIZED", "未授权", 401)

        self.token_blacklist[jti] = datetime.utcnow().isoformat() + "Z"
        self._log_audit("logout", username, audit_ip, "success", "Token blacklisted")
        return self._success_response(None, 200)

    def is_token_valid(self, token):
        if not token:
            return False
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return False
            payload = json.loads(parts[1])
            jti = payload.get("jti")
            exp = payload.get("exp")
        except (json.JSONDecodeError, IndexError, ValueError):
            return False

        if jti in self.token_blacklist:
            return False

        if exp:
            if isinstance(exp, str):
                exp_dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            else:
                exp_dt = datetime.utcfromtimestamp(exp)
            if datetime.utcnow() > exp_dt:
                return False
        return True


# ─── Fixtures ───

@pytest.fixture()
def sample_user():
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(b"Test@1234", bcrypt.gensalt(rounds=12)).decode("utf-8")
    return {
        "id": user_id, "username": "testuser", "password_hash": password_hash,
        "email": "test@example.com", "role": "user", "status": "active",
    }


@pytest.fixture()
def admin_user_fixture():
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(b"Admin@1234", bcrypt.gensalt(rounds=12)).decode("utf-8")
    return {
        "id": user_id, "username": "adminuser", "password_hash": password_hash,
        "email": "admin@example.com", "role": "admin", "status": "active",
    }


@pytest.fixture()
def auth_app(sample_user, login_attempts, account_lockouts, ip_rate_limits, token_blacklist, audit_log):
    users = {sample_user["username"]: sample_user}
    return InMemoryAuthApp(
        users=users, login_attempts=login_attempts, account_lockouts=account_lockouts,
        ip_rate_limits=ip_rate_limits, token_blacklist=token_blacklist, audit_log=audit_log,
    )


@pytest.fixture()
def auth_app_multi_user(sample_user, admin_user_fixture, login_attempts, account_lockouts, ip_rate_limits, token_blacklist, audit_log):
    users = {sample_user["username"]: sample_user, admin_user_fixture["username"]: admin_user_fixture}
    return InMemoryAuthApp(
        users=users, login_attempts=login_attempts, account_lockouts=account_lockouts,
        ip_rate_limits=ip_rate_limits, token_blacklist=token_blacklist, audit_log=audit_log,
    )


# ─── Test Cases ───

# ── TC-040: POST /api/v1/auth/login with valid credentials → 200 ──

@pytest.mark.asyncio
async def test_tc_040_login_valid_credentials_returns_200(auth_app):
    """TC-040: Valid credentials → 200 with access_token, refresh_token, user info.

    Verifies: response 200, unified format {success, data, error}, token/user fields,
    NO HttpOnly Cookie set.
    """
    resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    body, status = resp[0]
    headers = resp[1] if len(resp) > 1 else {}

    assert status == 200
    assert body["success"] is True
    assert body["error"] is None

    data = body["data"]
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)
    assert data["expires_in"] == 86400
    assert data["user"]["id"] is not None
    assert data["user"]["username"] == "testuser"
    assert data["user"]["role"] == "user"

    assert "set-cookie" not in {k.lower() for k in headers}


@pytest.mark.asyncio
async def test_tc_040_login_valid_credentials_response_time(auth_app):
    """TC-040: Login request completes within 2 seconds."""
    start = time.monotonic()
    auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    assert time.monotonic() - start < 2.0


# ── TC-041: POST /api/v1/auth/login with invalid credentials → 401 ──

@pytest.mark.asyncio
async def test_tc_041_login_invalid_username(auth_app):
    """TC-041: Non-existent username → 401 INVALID_CREDENTIALS."""
    resp = auth_app.post_login({"username": "nonexistent", "password": "Test@1234"})
    body, status = resp[0]
    assert status == 401
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert body["error"]["message"] == "用户名或密码错误"


@pytest.mark.asyncio
async def test_tc_041_login_wrong_password(auth_app):
    """TC-041: Valid username, wrong password → 401 INVALID_CREDENTIALS."""
    resp = auth_app.post_login({"username": "testuser", "password": "WrongPass@1"})
    body, status = resp[0]
    assert status == 401
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert body["error"]["message"] == "用户名或密码错误"


@pytest.mark.asyncio
async def test_tc_041_login_does_not_distinguish_error_type(auth_app):
    """TC-041: Error response identical for wrong username vs wrong password."""
    resp1 = auth_app.post_login({"username": "nonexistent", "password": "Test@1234"})
    resp2 = auth_app.post_login({"username": "testuser", "password": "WrongPass@1"})
    err1 = resp1[0][0]["error"]
    err2 = resp2[0][0]["error"]
    assert err1["code"] == err2["code"]
    assert err1["message"] == err2["message"]


# ── TC-042: POST /api/v1/auth/login after 5 failures → 423 ──

@pytest.mark.asyncio
async def test_tc_042_account_locked_after_5_failures(auth_app):
    """TC-042: 5 consecutive wrong passwords → 6th returns 423 ACCOUNT_LOCKED."""
    for i in range(5):
        resp = auth_app.post_login({"username": "testuser", "password": "WrongPass@1"})
        body, status = resp[0]
        assert status == 401
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    body, status = resp[0]
    assert status == 423
    assert body["error"]["code"] == "ACCOUNT_LOCKED"
    assert body["error"]["message"] == "账号已被临时锁定，请 15 分钟后再试"


@pytest.mark.asyncio
async def test_tc_042_lockout_expires_after_15_minutes(auth_app):
    """TC-042: Lockout expires after 15 minutes, login succeeds."""
    for _ in range(5):
        auth_app.post_login({"username": "testuser", "password": "WrongPass@1"})
    resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    assert resp[0][1] == 423

    auth_app.now += 901
    resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    assert resp[0][1] == 200


# ── TC-043: POST /api/v1/auth/refresh with valid refresh_token → 200 ──

@pytest.mark.asyncio
async def test_tc_043_refresh_valid_token_returns_new_pair(auth_app):
    """TC-043: Valid refresh_token → new access_token + new refresh_token."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    original_refresh = login_resp[0][0]["data"]["refresh_token"]
    original_access = login_resp[0][0]["data"]["access_token"]

    refresh_resp = auth_app.post_refresh({"refresh_token": original_refresh})
    body, status = refresh_resp
    assert status == 200
    assert body["data"]["access_token"] != original_access
    assert body["data"]["refresh_token"] != original_refresh
    assert body["data"]["expires_in"] == 86400


@pytest.mark.asyncio
async def test_tc_043_refresh_invalidates_original_token(auth_app):
    """TC-043: After refresh, original refresh_token rejected (single-use)."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    original_refresh = login_resp[0][0]["data"]["refresh_token"]

    auth_app.post_refresh({"refresh_token": original_refresh})

    reuse_resp = auth_app.post_refresh({"refresh_token": original_refresh})
    body, status = reuse_resp
    assert status == 401
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert body["error"]["message"] == "刷新令牌已过期"


# ── TC-044: POST /api/v1/auth/refresh with expired refresh_token → 401 ──

@pytest.mark.asyncio
async def test_tc_044_refresh_expired_token(auth_app):
    """TC-044: Expired refresh_token → 401 INVALID_TOKEN."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    refresh_token = login_resp[0][0]["data"]["refresh_token"]

    auth_app.now += 86401

    resp = auth_app.post_refresh({"refresh_token": refresh_token})
    body, status = resp
    assert status == 401
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert body["error"]["message"] == "刷新令牌已过期"


@pytest.mark.asyncio
async def test_tc_044_refresh_invalid_token(auth_app):
    """TC-044: Non-existent refresh_token → 401."""
    resp = auth_app.post_refresh({"refresh_token": "not-a-valid-token"})
    body, status = resp
    assert status == 401
    assert body["error"]["code"] == "INVALID_TOKEN"


# ── TC-045: POST /api/v1/auth/logout with valid Authorization → 200 ──

@pytest.mark.asyncio
async def test_tc_045_logout_valid_token(auth_app):
    """TC-045: Logout → 200, token blacklisted."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    access_token = login_resp[0][0]["data"]["access_token"]

    assert auth_app.is_token_valid(access_token) is True

    logout_resp = auth_app.post_logout(access_token, audit_user="testuser")
    body, status = logout_resp
    assert status == 200
    assert body["success"] is True
    assert auth_app.is_token_valid(access_token) is False


@pytest.mark.asyncio
async def test_tc_045_logout_then_use_token_fails(auth_app):
    """TC-045: After logout, same token → 401."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    access_token = login_resp[0][0]["data"]["access_token"]

    auth_app.post_logout(access_token, audit_user="testuser")

    logout_retry = auth_app.post_logout(access_token, audit_user="testuser")
    assert logout_retry[0][1] == 401


# ── TC-046: Access auth endpoint without Authorization → 401 ──

@pytest.mark.asyncio
async def test_tc_046_logout_without_token(auth_app):
    """TC-046: logout without token → 401 UNAUTHORIZED."""
    resp = auth_app.post_logout("")
    body, status = resp
    assert status == 401
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"] == "未授权"


@pytest.mark.asyncio
async def test_tc_046_refresh_without_token(auth_app):
    """TC-046: refresh without refresh_token → 422 VALIDATION_ERROR."""
    resp = auth_app.post_refresh({})
    body, status = resp
    assert status == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"


# ── TC-047: IP rate limit — 11 requests in 1 minute → 11th returns 429 ──

@pytest.mark.asyncio
async def test_tc_047_ip_rate_limit(auth_app):
    """TC-047: 10 requests → OK, 11th → 429 RATE_LIMITED."""
    ip = "192.168.1.100"

    for i in range(10):
        resp = auth_app.post_login({"username": "nonexistent_user", "password": "SomePass@1"}, ip=ip)
        assert resp[0][1] != 429

    resp = auth_app.post_login({"username": "nonexistent_user", "password": "SomePass@1"}, ip=ip)
    body, status = resp[0]
    assert status == 429
    assert body["error"]["code"] == "RATE_LIMITED"
    assert body["error"]["message"] == "请求过于频繁，请稍后重试"


@pytest.mark.asyncio
async def test_tc_047_rate_limit_resets_after_window(auth_app):
    """TC-047: After 60s window, requests allowed again."""
    ip = "192.168.1.200"

    for _ in range(10):
        auth_app.post_login({"username": "nonexistent", "password": "Pass@1"}, ip=ip)
    resp = auth_app.post_login({"username": "x", "password": "y"}, ip=ip)
    assert resp[0][1] == 429

    auth_app.now += 61

    resp = auth_app.post_login({"username": "x", "password": "y"}, ip=ip)
    assert resp[0][1] != 429


# ── EC-005: Unified API Response Format ──

@pytest.mark.asyncio
async def test_ec_005_login_success_response_format(auth_app):
    """EC-005: Login success follows {success, data, error} schema."""
    resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    body, status = resp[0]
    assert "success" in body and "data" in body and "error" in body
    assert body["success"] is True
    assert body["data"] is not None
    assert body["error"] is None


@pytest.mark.asyncio
async def test_ec_005_login_error_response_format(auth_app):
    """EC-005: Login error follows {success, data, error} schema."""
    resp = auth_app.post_login({"username": "wrong", "password": "wrong"})
    body, status = resp[0]
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"] is not None
    assert "code" in body["error"] and "message" in body["error"]


@pytest.mark.asyncio
async def test_ec_005_refresh_response_format(auth_app):
    """EC-005: Refresh response follows unified schema."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    rt = login_resp[0][0]["data"]["refresh_token"]
    body, status = auth_app.post_refresh({"refresh_token": rt})
    assert "success" in body and "data" in body and "error" in body


@pytest.mark.asyncio
async def test_ec_005_logout_response_format(auth_app):
    """EC-005: Logout response follows unified schema."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    token = login_resp[0][0]["data"]["access_token"]
    body, status = auth_app.post_logout(token, audit_user="testuser")
    assert body["success"] is True
    assert body["data"] is None
    assert body["error"] is None


# ── EC-006: Audit Log Verification ──

@pytest.mark.asyncio
async def test_ec_006_login_success_logged(auth_app, audit_log):
    """EC-006: Successful login recorded in audit log."""
    auth_app.post_login({"username": "testuser", "password": "Test@1234"}, ip="10.0.0.1")
    entries = [e for e in audit_log if e["action"] == "login" and e["result"] == "success"]
    assert len(entries) >= 1
    assert entries[0]["username"] == "testuser"
    assert entries[0]["ip"] == "10.0.0.1"
    assert "timestamp" in entries[0]


@pytest.mark.asyncio
async def test_ec_006_login_failure_logged(auth_app, audit_log):
    """EC-006: Failed login recorded in audit log."""
    auth_app.post_login({"username": "testuser", "password": "WrongPass@1"}, ip="10.0.0.2")
    entries = [e for e in audit_log if e["action"] == "login" and e["result"] == "failure"]
    assert len(entries) >= 1
    assert entries[0]["username"] == "testuser"
    assert entries[0]["ip"] == "10.0.0.2"


@pytest.mark.asyncio
async def test_ec_006_logout_logged(auth_app, audit_log):
    """EC-006: Logout recorded in audit log."""
    login_resp = auth_app.post_login({"username": "testuser", "password": "Test@1234"})
    token = login_resp[0][0]["data"]["access_token"]
    auth_app.post_logout(token, audit_user="testuser", audit_ip="10.0.0.3")
    entries = [e for e in audit_log if e["action"] == "logout" and e["result"] == "success"]
    assert len(entries) >= 1
    assert entries[0]["username"] == "testuser"
    assert entries[0]["ip"] == "10.0.0.3"


@pytest.mark.asyncio
async def test_ec_006_nonexistent_user_login_logged(auth_app, audit_log):
    """EC-006: Non-existent user login recorded as failure."""
    auth_app.post_login({"username": "ghost_user", "password": "Pass@1"}, ip="10.0.0.4")
    entries = [e for e in audit_log if e["username"] == "ghost_user" and e["result"] == "failure"]
    assert len(entries) >= 1
    assert entries[0]["ip"] == "10.0.0.4"
