# Quickstart: Register & Login Authentication

## Prerequisites

- Node.js 18+ (for `npm` and `npx concurrently`)
- Python 3.12+ (with `pip`)

## Setup & Run

### 1. Clone and enter project

```bash
cd /tmp/spec_mode_dev
```

### 2. Install frontend dependencies

```bash
cd leecloud_platform/frontend
npm install
cd ..
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Start full-stack development environment

```bash
npm run dev
```

This uses `concurrently` to launch:
- **FastAPI** backend on `http://localhost:8000` (with `--reload`)
- **Vite** dev server on `http://localhost:5173` (proxies `/api/*` → `:8000`)

Press `Ctrl+C` to stop all processes.

### 5. Access the application

- Login page: `http://localhost:5173/auth/login`
- Register page: `http://localhost:5173/auth/register`
- API base: `http://localhost:8000/api/v1/auth/`

## API Quick Reference

```bash
# Login (API)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "youruser", "password": "YourPass1!"}'

# Login (Web)
# Visit http://localhost:5173/auth/login and fill form

# Register
# Visit http://localhost:5173/auth/register and fill form

# Refresh Token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh-token-from-login>"}'

# Logout (API)
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access-token>"
```

## Testing

```bash
# Backend tests
cd leecloud_platform/backend
pytest

# Frontend tests (once configured)
cd leecloud_platform/frontend
npm run test
```
