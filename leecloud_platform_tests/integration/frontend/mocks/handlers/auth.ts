// Spec: specs/001-register-login/spec.md → TC-040-TC-047, FR-022-FR-030
// MSW handlers for API auth endpoints matching auth_api.md contract

import { http, HttpResponse } from 'msw'

interface LoginRequest {
  username: string
  password: string
}

interface RefreshRequest {
  refresh_token: string
}

interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: { code: string; message: string; details?: Array<{ field: string; message: string }> } | null
}

interface LoginResponseData {
  access_token: string
  refresh_token: string
  expires_in: number
  user: {
    id: string
    username: string
    role: 'user' | 'admin'
  }
}

interface RefreshResponseData {
  access_token: string
  refresh_token: string
  expires_in: number
}

const MOCK_USER = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  username: 'testuser',
  password: 'Test@1234',
  role: 'user' as const,
}

let loginAttempts = 0
let accountLocked = false
const LOCK_DURATION = 15 * 60 * 1000
let lockExpiresAt = 0
let refreshTokens: Record<string, { userId: string; expiresAt: number }> = {}
let blacklistedTokens = new Set<string>()

function generateToken(): string {
  return `eyJhbGciOiJIUzI1NiJ9.${Buffer.from(JSON.stringify({ jti: crypto.randomUUID(), user_id: MOCK_USER.id, username: MOCK_USER.username, role: MOCK_USER.role, iat: Date.now(), exp: Date.now() + 86400000 })).toString('base64')}.sim_signature`
}

function generateRefreshToken(): string {
  return crypto.randomUUID()
}

function errorResponse(code: string, message: string, status: number, details?: Array<{ field: string; message: string }>): HttpResponse {
  const body: ApiResponse<null> = { success: false, data: null, error: { code, message, ...(details && { details }) } }
  return HttpResponse.json(body, { status })
}

function successResponse<T>(data: T, status = 200): HttpResponse {
  const body: ApiResponse<T> = { success: true, data, error: null }
  return HttpResponse.json(body, { status })
}

export const authHandlers = [
  http.post<never, LoginRequest>('/api/v1/auth/login', async ({ request }) => {
    const body = await request.json()

    if (!body?.username || !body?.password) {
      return errorResponse('VALIDATION_ERROR', 'Validation error details', 422, [
        { field: body?.username ? 'password' : 'username', message: body?.username ? '密码不能为空' : '用户名格式不正确，允许的字符：字母、数字、_.' }
      ])
    }

    if (accountLocked && Date.now() < lockExpiresAt) {
      return errorResponse('ACCOUNT_LOCKED', '账号已被临时锁定，请 15 分钟后再试', 423)
    }

    if (accountLocked && Date.now() >= lockExpiresAt) {
      accountLocked = false
      loginAttempts = 0
    }

    if (body.username !== MOCK_USER.username || body.password !== MOCK_USER.password) {
      loginAttempts++
      if (loginAttempts >= 5) {
        accountLocked = true
        lockExpiresAt = Date.now() + LOCK_DURATION
      }
      return errorResponse('INVALID_CREDENTIALS', '用户名或密码错误', 401)
    }

    loginAttempts = 0
    const accessToken = generateToken()
    const refreshToken = generateRefreshToken()
    refreshTokens[refreshToken] = { userId: MOCK_USER.id, expiresAt: Date.now() + 86400000 }

    return successResponse<LoginResponseData>({
      access_token: accessToken,
      refresh_token: refreshToken,
      expires_in: 86400,
      user: { id: MOCK_USER.id, username: MOCK_USER.username, role: MOCK_USER.role },
    })
  }),

  http.post<never, RefreshRequest>('/api/v1/auth/refresh', async ({ request }) => {
    const body = await request.json()

    if (!body?.refresh_token) {
      return errorResponse('VALIDATION_ERROR', 'Validation error details', 422, [
        { field: 'refresh_token', message: '刷新令牌不能为空' }
      ])
    }

    const tokenData = refreshTokens[body.refresh_token]
    if (!tokenData || Date.now() > tokenData.expiresAt) {
      if (tokenData) delete refreshTokens[body.refresh_token]
      return errorResponse('INVALID_TOKEN', '刷新令牌已过期', 401)
    }

    delete refreshTokens[body.refresh_token]

    const newAccessToken = generateToken()
    const newRefreshToken = generateRefreshToken()
    refreshTokens[newRefreshToken] = { userId: tokenData.userId, expiresAt: Date.now() + 86400000 }

    return successResponse<RefreshResponseData>({
      access_token: newAccessToken,
      refresh_token: newRefreshToken,
      expires_in: 86400,
    })
  }),

  http.post('/api/v1/auth/logout', async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = await request.json().catch(() => null)
    const token = authHeader?.replace('Bearer ', '') || body?.token

    if (!token) {
      return errorResponse('UNAUTHORIZED', '未授权', 401)
    }

    if (blacklistedTokens.has(token)) {
      return errorResponse('UNAUTHORIZED', '未授权', 401)
    }

    try {
      const parts = token.split('.')
      if (parts.length !== 3) throw new Error()
      const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString())
      blacklistedTokens.add(payload.jti)
    } catch {
      return errorResponse('UNAUTHORIZED', '未授权', 401)
    }

    return successResponse<null>(null)
  }),
]
