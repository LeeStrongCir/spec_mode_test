// Spec: specs/001-register-login/spec.md → TC-001-TC-008, EC-003, EC-004
// MSW Handlers: Register API mocking for frontend integration tests

import { http, HttpResponse } from 'msw';

interface RegisterRequest {
  username: string;
  password: string;
  confirm_password: string;
  email: string;
}

interface RegisteredUser {
  [username: string]: {
    id: string;
    username: string;
    email: string;
    password_hash: string;
  };
}

const registeredUsers: RegisteredUser = {};

function validateUsername(username: string): string | null {
  if (!username) return '请输入用户名';
  if (username.length < 2 || username.length > 32)
    return '用户名长度必须在 2-32 个字符之间';
  if (!/^[a-zA-Z0-9_\-\.]+$/.test(username))
    return '用户名格式不正确，允许的字符：字母、数字、_.-';
  return null;
}

function validatePassword(password: string): string | null {
  if (!password) return '请输入密码';
  if (password.length < 8) return '密码长度至少为 8 个字符';
  if (password.length > 32) return '密码长度最多为 32 个字符';
  return null;
}

function validateEmail(email: string): string | null {
  if (!email) return '请输入邮箱';
  if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email))
    return '邮箱格式不正确';
  return null;
}

function generateCsrfToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

export const registerHandlers = [
  // GET /api/v1/auth/csrf — returns CSRF cookie + token
  http.get('/api/v1/auth/csrf', () => {
    const token = generateCsrfToken();
    return HttpResponse.json(
      { success: true, data: { csrf_token: token }, error: null },
      {
        headers: {
          'Set-Cookie': `csrf_token=${token}; Path=/; Secure; SameSite=Strict; HttpOnly`,
        },
      },
    );
  }),

  // POST /api/v1/auth/register
  http.post<never, RegisterRequest>('/api/v1/auth/register', async ({ request, cookies }) => {
    // CSRF validation (FR-020)
    const csrfCookie = cookies?.['csrf_token'];
    const csrfHeader = request.headers.get('x-csrf-token');
    if (!csrfCookie || !csrfHeader || csrfCookie !== csrfHeader) {
      return HttpResponse.json(
        { success: false, data: null, error: { code: 'CSRF_MISMATCH', message: 'CSRF token 缺失或无效' } },
        { status: 403 },
      );
    }

    const body = await request.json().catch(() => null);
    if (!body) {
      return HttpResponse.json(
        { success: false, data: null, error: { code: 'VALIDATION_ERROR', message: '请求体无效' } },
        { status: 422 },
      );
    }

    // Field validation
    const usernameError = validateUsername(body.username);
    const passwordError = validatePassword(body.password);
    const emailError = validateEmail(body.email);

    if (usernameError || passwordError || emailError) {
      const details = [];
      if (usernameError) details.push({ field: 'username', message: usernameError });
      if (passwordError) details.push({ field: 'password', message: passwordError });
      if (emailError) details.push({ field: 'email', message: emailError });
      return HttpResponse.json(
        { success: false, data: null, error: { code: 'VALIDATION_ERROR', message: '验证失败', details } },
        { status: 422 },
      );
    }

    if (body.password !== body.confirm_password) {
      return HttpResponse.json(
        { success: false, data: null, error: { code: 'PASSWORD_MISMATCH', message: '两次输入的密码不一致' } },
        { status: 422 },
      );
    }

    if (body.username in registeredUsers) {
      return HttpResponse.json(
        { success: false, data: null, error: { code: 'DUPLICATE_USERNAME', message: '该用户名已被注册' } },
        { status: 409 },
      );
    }

    const userId = crypto.randomUUID();
    registeredUsers[body.username] = {
      id: userId,
      username: body.username,
      email: body.email,
      password_hash: `bcrypt$mock$${body.password}`,
    };

    return HttpResponse.json(
      {
        success: true,
        data: {
          user: { id: userId, username: body.username, email: body.email },
          redirect: '/console',
        },
        error: null,
      },
      {
        headers: {
          'Set-Cookie': `jwt_token=mock-jwt-${userId}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`,
        },
      },
    );
  }),

  // GET /auth/register — register page
  http.get('/auth/register', () => {
    return HttpResponse.html(`<!DOCTYPE html>
<html>
<head><title>注册 - LeeCloud</title></head>
<body>
  <h1>注册新账户</h1>
  <form>
    <input type="text" name="username" id="username" placeholder="用户名">
    <input type="password" name="password" id="password" placeholder="密码">
    <input type="password" name="confirm_password" id="confirm_password" placeholder="确认密码">
    <input type="email" name="email" id="email" placeholder="邮箱">
    <button type="submit">注册</button>
  </form>
  <a href="/auth/login">已有账户？返回登录</a>
</body>
</html>`);
  }),

  // GET /auth/login — login page
  http.get('/auth/login', () => {
    return HttpResponse.html('<h1>登录页</h1>');
  }),

  // GET /console — dashboard
  http.get('/console', () => {
    return HttpResponse.html('<h1>控制台</h1>');
  }),
];
