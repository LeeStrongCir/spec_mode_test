# API Contracts: Authentication

## POST /api/auth/login

Authenticate a user with username and password.

### Request

**Headers**:
| Header | Required | Description |
|--------|----------|-------------|
| `X-CSRF-Token` | Yes | CSRF token from `/api/auth/csrf` |
| `Content-Type` | Yes | `application/json` |
| `X-Forwarded-For` | No | Client IP (for rate limiting behind proxies) |

**Body** (`application/json`):
```json
{
  "username": "string (3-32 chars, trimmed)",
  "password": "string (8-32 chars)",
  "rememberMe": "boolean (default: false)"
}
```

### Response

**200 OK** — Authentication successful
```json
{
  "success": true,
  "redirect": "/console"
}
```
**Set-Cookie**: `auth_token=<JWT>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=86400` (or 2592000 if rememberMe)
**Set-Cookie**: `csrf_token=<token>; SameSite=Strict; Path=/; Max-Age=86400`

**400 Bad Request** — Validation error
```json
{
  "success": false,
  "error": "Validation failed",
  "fields": {
    "username": ["Please enter username"],
    "password": ["Please enter password"]
  }
}
```

**401 Unauthorized** — Invalid credentials or account locked
```json
{
  "success": false,
  "error": "Username or password is incorrect"
}
```
Or (when locked):
```json
{
  "success": false,
  "error": "Account temporarily locked, please try again in 15 minutes"
}
```

**403 Forbidden** — Invalid or missing CSRF token
```json
{
  "success": false,
  "error": "CSRF token validation failed"
}
```

**429 Too Many Requests** — IP rate limit exceeded
```json
{
  "success": false,
  "error": "Request too frequent, please try again later"
}
```

---

## POST /api/auth/register

Create a new user account and auto-login.

### Request

**Headers**:
| Header | Required | Description |
|--------|----------|-------------|
| `X-CSRF-Token` | Yes | CSRF token from `/api/auth/csrf` |
| `Content-Type` | Yes | `application/json` |

**Body** (`application/json`):
```json
{
  "username": "string (3-32 chars, trimmed)",
  "password": "string (8-32 chars)",
  "confirmPassword": "string",
  "email": "string (valid email format)"
}
```

### Response

**201 Created** — Registration successful, user auto-logged in
```json
{
  "success": true,
  "redirect": "/console"
}
```
**Set-Cookie**: `auth_token=<JWT>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=86400`

**400 Bad Request** — Validation error
```json
{
  "success": false,
  "error": "Validation failed",
  "fields": {
    "username": ["Please enter username"],
    "password": ["Password must be 8-32 characters..."],
    "confirmPassword": ["Passwords do not match"],
    "email": ["Invalid email format"]
  }
}
```

**409 Conflict** — Username already exists
```json
{
  "success": false,
  "error": "This username is already registered",
  "fields": {
    "username": ["This username is already registered"]
  }
}
```

**403 Forbidden** — Invalid or missing CSRF token
```json
{
  "success": false,
  "error": "CSRF token validation failed"
}
```

---

## POST /api/auth/logout

Sign out the current user by clearing the authentication token.

### Request

**Headers**:
| Header | Required | Description |
|--------|----------|-------------|
| `X-CSRF-Token` | Yes | CSRF token |
| `Cookie` | Yes | `auth_token=<JWT>` (valid JWT required) |

### Response

**200 OK** — Logout successful
```json
{
  "success": true,
  "redirect": "/auth/login"
}
```
**Set-Cookie**: `auth_token=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0`

---

## GET /api/auth/csrf

Retrieve a CSRF token for the current session.

### Request

No body required. Session cookie or auth cookie accepted.

### Response

**200 OK**
```json
{
  "csrfToken": "<token-string>"
}
```

---

## GET /api/health

Health check endpoint (public, no auth required).

### Response

**200 OK**
```json
{
  "status": "ok",
  "timestamp": "2026-05-11T12:00:00Z"
}
```
