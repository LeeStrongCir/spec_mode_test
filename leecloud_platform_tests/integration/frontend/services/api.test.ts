// Spec: specs/001-register-login/spec.md → TC-040-TC-047, FR-022-FR-030
// API Service layer integration tests (Vitest + MSW)

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { authHandlers } from '../mocks/handlers/auth'

const server = setupServer(...authHandlers)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
beforeEach(() => server.resetHandlers())

interface ApiResponse<T> {
  success: boolean
  data: T | null
  error: { code: string; message: string } | null
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: { id: string; username: string; role: string }
}

interface RefreshResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

async function loginApi(username: string, password: string): Promise<ApiResponse<LoginResponse>> {
  const res = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  return res.json()
}

async function refreshApi(refreshToken: string): Promise<ApiResponse<RefreshResponse>> {
  const res = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  return res.json()
}

async function logoutApi(token: string): Promise<ApiResponse<null>> {
  const res = await fetch('/api/v1/auth/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  })
  return res.json()
}

describe('API Service Layer — Auth Endpoints', () => {
  describe('loginApi()', () => {
    it('TC-040: returns parsed response with access_token, refresh_token, user on valid credentials', async () => {
      const result = await loginApi('testuser', 'Test@1234')

      expect(result.success).toBe(true)
      expect(result.error).toBeNull()
      expect(result.data).not.toBeNull()
      expect(result.data!.access_token).toBeDefined()
      expect(typeof result.data!.access_token).toBe('string')
      expect(result.data!.refresh_token).toBeDefined()
      expect(result.data!.expires_in).toBe(86400)
      expect(result.data!.user.id).toBeDefined()
      expect(result.data!.user.username).toBe('testuser')
      expect(result.data!.user.role).toBe('user')
    })

    it('TC-041: returns 401 INVALID_CREDENTIALS on wrong password', async () => {
      const result = await loginApi('testuser', 'WrongPass@1')

      expect(result.success).toBe(false)
      expect(result.data).toBeNull()
      expect(result.error!.code).toBe('INVALID_CREDENTIALS')
      expect(result.error!.message).toBe('用户名或密码错误')
    })

    it('TC-041: returns 401 on non-existent username', async () => {
      const result = await loginApi('nonexistent', 'AnyPass@1')

      expect(result.success).toBe(false)
      expect(result.error!.code).toBe('INVALID_CREDENTIALS')
    })

    it('TC-042: returns 423 ACCOUNT_LOCKED after 5 failed attempts', async () => {
      for (let i = 0; i < 5; i++) {
        await loginApi('testuser', 'WrongPass@1')
      }
      const result = await loginApi('testuser', 'Test@1234')

      expect(result.success).toBe(false)
      expect(result.error!.code).toBe('ACCOUNT_LOCKED')
      expect(result.error!.message).toBe('账号已被临时锁定，请 15 分钟后再试')
    })
  })

  describe('refreshApi()', () => {
    it('TC-043: returns new token pair on valid refresh_token', async () => {
      const loginResult = await loginApi('testuser', 'Test@1234')
      const originalRefreshToken = loginResult.data!.refresh_token
      const originalAccessToken = loginResult.data!.access_token

      const result = await refreshApi(originalRefreshToken)

      expect(result.success).toBe(true)
      expect(result.data!.access_token).not.toBe(originalAccessToken)
      expect(result.data!.refresh_token).not.toBe(originalRefreshToken)
      expect(result.data!.expires_in).toBe(86400)
    })

    it('TC-043: rejects reused refresh_token (single-use)', async () => {
      const loginResult = await loginApi('testuser', 'Test@1234')
      const originalRefreshToken = loginResult.data!.refresh_token

      await refreshApi(originalRefreshToken)
      const reuseResult = await refreshApi(originalRefreshToken)

      expect(reuseResult.success).toBe(false)
      expect(reuseResult.error!.code).toBe('INVALID_TOKEN')
      expect(reuseResult.error!.message).toBe('刷新令牌已过期')
    })
  })

  describe('logoutApi()', () => {
    it('TC-045: returns success response on valid token', async () => {
      const loginResult = await loginApi('testuser', 'Test@1234')
      const token = loginResult.data!.access_token

      const result = await logoutApi(token)

      expect(result.success).toBe(true)
      expect(result.data).toBeNull()
      expect(result.error).toBeNull()
    })

    it('TC-045: rejects already-logged-out token', async () => {
      const loginResult = await loginApi('testuser', 'Test@1234')
      const token = loginResult.data!.access_token

      await logoutApi(token)
      const retryResult = await logoutApi(token)

      expect(retryResult.success).toBe(false)
      expect(retryResult.error!.code).toBe('UNAUTHORIZED')
    })

    it('TC-046: returns 401 when called without token', async () => {
      const result = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }).then(r => r.json())

      expect(result.success).toBe(false)
      expect(result.error!.code).toBe('UNAUTHORIZED')
      expect(result.error!.message).toBe('未授权')
    })
  })

  describe('EC-005: Unified API Response Format', () => {
    it('every response contains success, data, error fields', async () => {
      const loginResp = await loginApi('testuser', 'Test@1234')
      expect('success' in loginResp).toBe(true)
      expect('data' in loginResp).toBe(true)
      expect('error' in loginResp).toBe(true)

      const refreshToken = loginResp.data!.refresh_token
      const refreshResp = await refreshApi(refreshToken)
      expect('success' in refreshResp).toBe(true)
      expect('data' in refreshResp).toBe(true)
      expect('error' in refreshResp).toBe(true)

      const logoutResp = await logoutApi(refreshResp.data!.access_token)
      expect('success' in logoutResp).toBe(true)
      expect('data' in logoutResp).toBe(true)
      expect('error' in logoutResp).toBe(true)
    })

    it('error responses contain code and message string fields', async () => {
      const resp = await loginApi('wrong', 'wrong')
      expect(resp.error!.code).toBeDefined()
      expect(typeof resp.error!.code).toBe('string')
      expect(resp.error!.message).toBeDefined()
      expect(typeof resp.error!.message).toBe('string')
    })
  })
})
