# Data Model: Register & Login Authentication

## Entity: User (`users` table)

The primary table representing registered user accounts.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID (string) | PK, NOT NULL | Unique identifier for each user |
| `username` | str (max 32) | UNIQUE, NOT NULL | Login identifier, alphanumeric + `_` `-` `.` |
| `password_hash` | str | NOT NULL | BCrypt hash of the password |
| `email` | str (max 255) | UNIQUE, NOT NULL | User email address |
| `status` | str (enum) | NOT NULL, default `'active'` | `'active'` or `'locked'` |
| `role` | str (enum) | NOT NULL, default `'user'` | `'admin'` or `'user'` |
| `last_login_at` | datetime | NULLABLE | Timestamp of last successful login (UTC) |
| `last_login_ip` | str (max 45) | NULLABLE | IP address of last successful login |
| `failed_login_count` | int | NOT NULL, default `0` | Consecutive failed login attempts |
| `last_failed_at` | datetime | NULLABLE | Timestamp of most recent failed attempt (UTC) |
| `locked_until` | datetime | NULLABLE | Account lockout expiry (UTC) — null if not locked |
| `created_at` | datetime | NOT NULL | Account creation timestamp (UTC) |

**Validation Rules** (from spec):
- `username`: unique, matches `^[a-zA-Z0-9_\-\.]{2,32}$`, no HTML/JS/SQL chars (XSS/注入防护 edge case)
- `password_hash`: BCrypt with cost factor >= 12, derived via `passlib[bcrypt]`
- `email`: unique, valid email format (RFC 5322 simplified: `local@domain.tld`)
- `status`: transitions to `locked` only via repeated failures, resets to `active` after lockout expires or admin action
- `role`: set at creation (`user` default), admin can update

**State Transitions**:
```
[active] ───(5 consecutive failures)───> [locked]
   ^                                        │
   │                                        │ (15 minutes elapsed)
   └────────(lockout expires)───────────────┘
```

## Entity: Token Blacklist (`token_blacklist` table)

Tracks JWT token identifiers (jti) that have been revoked (API logout).

| Field | Type | Constraints | Description |
|---|---|---|---|
| `jti` | str (max 64) | PK, NOT NULL | JWT ID claim — unique token identifier |
| `expires_at` | datetime | NOT NULL | Token natural expiration (for cleanup) |
| `revoked_at` | datetime | NOT NULL | Time when token was blacklisted |

**Validation Rules**:
- `jti` must be a valid UUID format
- `expires_at` must be in the future at time of insertion
- Automatically cleaned up when `expires_at` has passed

## Runtime State (Python dict — NOT tables)

The following state is held in-memory (no persistence between restarts), per Constitution's "Python 内存 dict (不引Redis)" constraint:

### `login_attempts` dict
```python
{
    "username:<username>": {
        "count": int,           # consecutive failure count
        "last_attempt": float,  # Unix timestamp
    },
    "ip:<ip_address>": {
        "timestamps": [float],  # list of request timestamps within window
    }
}
```

### `account_lockouts` dict
```python
{
    "username:<username>": {
        "locked_until": float,  # Unix timestamp when lockout expires
    }
}
```

## Relationships

```
User (1) ────────┬──────── (N) Audit Log entry (FR-013) (*)
                 │
                 └── Token Blacklist entries (via user_id claim in JWT)

(*) Audit log entries are not stored in DB but written asynchronously
    via FastAPI BackgroundTasks — see FR-013 assumptions.
```

---
**Notes**:
- All timestamps stored in UTC
- No foreign keys (SQLite performance; referential integrity handled at app level)
- `id` uses UUID v4 for uniqueness without coordination
