# Spec: specs/001-register-login/spec.md → TC-001-TC-008, EC-003, EC-004
# Test Infrastructure Fixtures for Auth Integration Tests

import re
import uuid
import time
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
import pytest_asyncio
import bcrypt
import jwt
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, Enum as SAEnum, Integer, String, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


# ─── In-memory state (simulating runtime dicts from data-model.md) ───

@pytest.fixture
def login_attempts():
    """Fresh login attempts dict per test — simulates Redis-like in-memory state."""
    return {}


@pytest.fixture
def account_lockouts():
    """Fresh account lockouts dict per test."""
    return {}


@pytest.fixture
def ip_rate_limits():
    """Fresh IP rate limit tracking dict per test."""
    return {}


@pytest.fixture
def csrf_tokens():
    """Fresh CSRF token store per test."""
    return {}


@pytest.fixture
def token_blacklist():
    """Fresh token blacklist dict per test."""
    return {}


@pytest.fixture
def audit_log():
    """Collect audit log entries for verification."""
    return []


# ─── Test Data Factory ───

class UserFactory:
    """Create test user records with sensible defaults."""

    TEST_USERS: dict = {}

    @classmethod
    def create(
        cls,
        username: str = "testuser",
        password: str = "Test@1234",
        email: str = "test@example.com",
        role: str = "user",
        status: str = "active",
    ) -> dict:
        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=12)
        ).decode("utf-8")
        now = datetime.utcnow().isoformat() + "Z"
        user = {
            "id": user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "role": role,
            "status": status,
            "failed_login_count": 0,
            "last_login_at": None,
            "last_login_ip": None,
            "locked_until": None,
            "created_at": now,
        }
        cls.TEST_USERS[username] = user
        return user

    @classmethod
    def get(cls, username: str) -> Optional[dict]:
        return cls.TEST_USERS.get(username)

    @classmethod
    def verify_password(cls, username: str, password: str) -> bool:
        user = cls.get(username)
        if not user:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        )

    @classmethod
    def clear(cls):
        cls.TEST_USERS.clear()


@pytest.fixture(autouse=True)
def reset_user_factory():
    """Auto-reset UserFactory between tests."""
    UserFactory.clear()
    yield
    UserFactory.clear()


# ─── JWT Helpers ───

JWT_SECRET = "test-secret-key"
JWT_ALGORITHM = "HS256"


def create_jwt(
    user: dict,
    expires_in: int = 86400,
    extra_claims: Optional[dict] = None,
) -> str:
    now = datetime.utcnow()
    payload = {
        "jti": str(uuid.uuid4()),
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def create_expired_jwt(user: dict) -> str:
    """Create a JWT that is already expired."""
    now = datetime.utcnow()
    payload = {
        "jti": str(uuid.uuid4()),
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": now - timedelta(seconds=7200),
        "exp": now - timedelta(seconds=3600),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ─── CSRF Helpers ───

def generate_csrf_token() -> str:
    """Generate a random CSRF token (32-byte base64)."""
    return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")


# ─── Pytest Fixtures ───

@pytest.fixture()
def standard_user():
    """Create a standard test user."""
    return UserFactory.create()


@pytest.fixture()
def admin_user():
    """Create an admin test user."""
    return UserFactory.create(
        username="adminuser",
        password="Admin@1234",
        email="admin@example.com",
        role="admin",
    )


@pytest.fixture()
def valid_jwt(standard_user):
    """Return a valid JWT for the standard user."""
    return create_jwt(standard_user)


DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"

Base = DeclarativeBase()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(32), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    status = Column(SAEnum("active", "locked"), nullable=False, default="active")
    role = Column(SAEnum("admin", "user"), nullable=False, default="user")
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    last_failed_at = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def db_session():
    async_engine = create_async_engine(DATABASE_URL, echo=False)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await async_engine.dispose()


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def async_app(db_session, login_attempts, account_lockouts, csrf_tokens, token_blacklist, audit_log):
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, RedirectResponse, Response
    from pydantic import BaseModel, field_validator

    app = FastAPI(title="LeeCloud Test App")

    _runtime_users: dict = {}

    class RegisterRequest(BaseModel):
        username: str
        password: str
        confirm_password: str
        email: str

        @field_validator("username")
        @classmethod
        def chk_username(cls, v):
            if not v:
                raise ValueError("请输入用户名")
            if len(v) < 2 or len(v) > 32:
                raise ValueError("用户名长度必须在 2-32 个字符之间")
            if not re.match(r"^[a-zA-Z0-9_\-\.]+$", v):
                raise ValueError("用户名格式不正确")
            return v

        @field_validator("password")
        @classmethod
        def chk_password(cls, v):
            if not v:
                raise ValueError("请输入密码")
            if len(v) < 8:
                raise ValueError("密码长度至少为 8 个字符")
            if len(v) > 32:
                raise ValueError("密码长度最多为 32 个字符")
            return v

        @field_validator("email")
        @classmethod
        def chk_email(cls, v):
            if not v:
                raise ValueError("请输入邮箱")
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
                raise ValueError("邮箱格式不正确")
            return v

    def _hash_pw(raw: str) -> str:
        salt = secrets.token_hex(16)
        return f"bcrypt${salt}${hashlib.sha256(raw.encode()).hexdigest()}"

    def _is_authed(request: Request) -> bool:
        tok = request.cookies.get("jwt_token")
        if not tok:
            return False
        try:
            return jwt.decode(tok, JWT_SECRET, algorithms=[JWT_ALGORITHM]) is not None
        except Exception:
            return False

    def _get_csrf_cookie(request: Request) -> str | None:
        return request.cookies.get("csrf_token")

    def _register_page_html(csrf: str) -> str:
        return (
            "<!DOCTYPE html><html><head><title>注册 - LeeCloud</title></head><body>"
            '<h1>注册新账户</h1>'
            f'<form action="/api/v1/auth/register" method="POST">'
            f'<input type="hidden" name="csrf_token" value="{csrf}">'
            '<input type="text" name="username" id="username" placeholder="用户名">'
            '<input type="password" name="password" id="password" placeholder="密码">'
            '<input type="password" name="confirm_password" id="confirm_password" placeholder="确认密码">'
            '<input type="email" name="email" id="email" placeholder="邮箱">'
            '<button type="submit">注册</button>'
            "</form>"
            '<a href="/auth/login">已有账户？返回登录</a>'
            "</body></html>"
        )

    @app.get("/auth/register")
    async def get_register(request: Request):
        if _is_authed(request):
            return RedirectResponse(url="/console", status_code=302)
        csrf = generate_csrf_token()
        html = _register_page_html(csrf)
        resp = HTMLResponse(content=html)
        resp.set_cookie("csrf_token", csrf, path="/", httponly=True, secure=True, samesite="strict")
        return resp

    @app.get("/auth/login")
    async def get_login(request: Request):
        if _is_authed(request):
            return RedirectResponse(url="/console", status_code=302)
        return HTMLResponse(content="<h1>登录页</h1>")

    @app.get("/console")
    async def get_console():
        return HTMLResponse(content="<h1>控制台</h1>")

    @app.get("/api/v1/auth/csrf")
    async def csrf_endpoint(response: Response):
        tok = generate_csrf_token()
        response.set_cookie("csrf_token", tok, path="/", httponly=True, secure=True, samesite="strict")
        return {"success": True, "data": {"csrf_token": tok}, "error": None}

    @app.post("/api/v1/auth/register")
    async def post_register(request: Request, body: RegisterRequest, response: Response):
        cookie_csrf = _get_csrf_cookie(request)
        header_csrf = request.headers.get("x-csrf-token")
        if not cookie_csrf or not header_csrf or cookie_csrf != header_csrf:
            return Response(
                status_code=403,
                content='{"success":false,"data":null,"error":{"code":"CSRF_MISMATCH","message":"CSRF token 缺失或无效"}}',
                media_type="application/json",
            )
        if body.username in _runtime_users:
            return Response(
                status_code=409,
                content='{"success":false,"data":null,"error":{"code":"DUPLICATE_USERNAME","message":"该用户名已被注册"}}',
                media_type="application/json",
            )
        if body.password != body.confirm_password:
            return Response(
                status_code=422,
                content='{"success":false,"data":null,"error":{"code":"PASSWORD_MISMATCH","message":"两次输入的密码不一致"}}',
                media_type="application/json",
            )
        uid = str(uuid.uuid4())
        _runtime_users[body.username] = {
            "id": uid, "username": body.username,
            "password_hash": _hash_pw(body.password), "email": body.email,
            "status": "active", "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        now_ts = int(datetime.now(timezone.utc).timestamp())
        access = jwt.encode(
            {"jti": str(uuid.uuid4()), "sub": uid, "username": body.username,
             "role": "user", "iat": now_ts, "exp": now_ts + 86400},
            JWT_SECRET, algorithm=JWT_ALGORITHM,
        )
        response.set_cookie(
            "jwt_token", access, path="/", httponly=True, secure=True, samesite="strict", max_age=86400,
        )
        return {"success": True, "data": {"user": {"id": uid, "username": body.username, "email": body.email}, "redirect": "/console"}, "error": None}

    yield app


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def async_client(async_app):
    transport = ASGITransport(app=async_app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=False) as c:
        yield c


@pytest_asyncio.fixture(loop_scope="function", scope="function")
async def create_user(db_session):
    async def _create(
        username: str = "testuser",
        password: str = "Test@1234",
        email: str = "testuser@example.com",
        status: str = "active",
        role: str = "user",
    ) -> User:
        salt = secrets.token_hex(16)
        pw_hash = f"bcrypt${salt}${hashlib.sha256(password.encode()).hexdigest()}"
        user = User(
            id=str(uuid.uuid4()), username=username, password_hash=pw_hash,
            email=email, status=status, role=role,
        )
        db_session.add(user)
        await db_session.flush()
        return user
    return _create


@pytest.fixture()
def expired_jwt(standard_user):
    """Return an expired JWT for the standard user."""
    return create_expired_jwt(standard_user)


@pytest.fixture()
def valid_auth_cookies(valid_jwt):
    """Return a dict of cookies simulating a valid logged-in session."""
    return {"jwt_token": valid_jwt}
