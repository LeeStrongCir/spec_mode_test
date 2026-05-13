# Auth API Contract: Register & Login Authentication

Base URL: `/api/v1/auth`
Version: v1
Protocol: HTTP/1.1 or HTTP/2 over TLS

---

## POST /login

Authenticate user via API (for external service consumption).

### Request
```json
{
  "username": "string (2-32 chars, alphanumeric + _ . -)",
  "password": "string (8-32 chars)"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "access_token": "JWT string (with jti claim)",
    "refresh_token": "string (UUID format, single-use)",
    "expires_in": 86400,
    "user": {
      "id": "uuid",
      "username": "string",
      "role": "user | admin"
    }
  },
  "error": null
}
```

### Error Responses

**401 Unauthorized — Invalid credentials**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "用户名或密码错误"
  }
}
```

**423 Locked — Account temporarily locked**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ACCOUNT_LOCKED",
    "message": "账号已被临时锁定，请 15 分钟后再试"
  }
}
```

**429 Too Many Requests — IP rate limit exceeded**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "RATE_LIMITED",
    "message": "请求过于频繁，请稍后重试"
  }
}
```

**422 Validation Error — Request body validation failed**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation error details",
    "details": [
      {
        "field": "username",
        "message": "用户名格式不正确，允许的字符：字母、数字、_."
      }
    ]
  }
}
```

### Rate Limits
- IP-based: 10 requests / minute per IP address
- Account-based: 5 consecutive failures → 15 minute lockout

---

## POST /refresh

Renew JWT Token using a valid refresh token.

### Request
```json
{
  "refresh_token": "string (UUID format)"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "access_token": "new JWT string",
    "refresh_token": "new refresh token (old one invalidated)",
    "expires_in": 86400
  },
  "error": null
}
```

### Error Responses

**401 Unauthorized — Invalid or expired refresh token**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_TOKEN",
    "message": "刷新令牌已过期"
  }
}
```

---

## POST /logout

Revoke JWT Token and add to blacklist.

### Request Headers
```
Authorization: Bearer <access_token>
```
OR request body:
```json
{
  "token": "JWT string (optional if Authorization header used)"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "data": null,
  "error": null
}
```

### Error Responses

**401 Unauthorized — No valid authentication provided**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "未授权"
  }
}
```

---

## GET /csrf (Supporting Endpoint)

Retrieve a CSRF token for web form protection.

### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "csrf_token": "string (random 32-byte base64)"
  },
  "error": null
}
```

### Cookie Behavior
The response also sets a `Set-Cookie` header:
```
Set-Cookie: csrf_token=<value>; Path=/; Secure; SameSite=Strict; HttpOnly
```

---

## Common Response Format (FR-030)

All API responses follow this unified JSON schema:

```json
{
  "success": "boolean (true on success, false on error)",
  "data": "object | null (response payload on success, null on error)",
  "error": "object | null ({ code, message } on error, null on success)"
}
```

**Error code enumeration**:
| Code | HTTP Status | Description |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Wrong username or password |
| `ACCOUNT_LOCKED` | 423 | Account temporarily locked after failures |
| `RATE_LIMITED` | 429 | Too many requests from this IP |
| `INVALID_TOKEN` | 401 | Token expired, malformed, or blacklisted |
| `UNAUTHORIZED` | 401 | No valid authentication (missing/invalid credentials) |
| `VALIDATION_ERROR` | 422 | Request body failed Pydantic validation |
| `CSRF_MISMATCH` | 403 | CSRF token missing or doesn't match cookie |
