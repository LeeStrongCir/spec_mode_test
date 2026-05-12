# Data Model: Register and Login

## Entities

### User

Represents a registered user account on the platform.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID (auto) | Primary Key | Unique internal identifier |
| `username` | String (3-32 chars) | Unique, indexed, trimmed | Display name and login credential |
| `email` | String (max 255) | Unique, indexed | Contact email address |
| `passwordHash` | String (bcrypt) | Not nullable | BCrypt hash of user password (cost ≥ 12) |
| `status` | Enum | `active` \| `locked` | Account state |
| `role` | Enum | `user` \| `admin` | Access level |
| `failedLoginCount` | Integer | Default: 0 | Consecutive failed login attempts |
| `lastFailedLoginAt` | DateTime | Nullable | Time of most recent failed login |
| `lastLoginAt` | DateTime | Nullable | Time of most recent successful login |
| `lastLoginIp` | String (max 45) | Nullable | IP address of most recent login |
| `createdAt` | DateTime | Auto-set on creation | Account registration timestamp |
| `updatedAt` | DateTime | Auto-updated | Last modification timestamp |

### AuditLog

Records all authentication operations for security auditing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID (auto) | Primary Key | Unique log entry identifier |
| `userId` | UUID (FK → User) | Nullable (null for failed username-not-found) | Associated user |
| `username` | String | Not nullable | Attempted username (always recorded) |
| `action` | Enum | `login` \| `logout` \| `register` | Operation type |
| `result` | Enum | `success` \| `failure` \| `locked` | Outcome |
| `ipAddress` | String (max 45) | Not nullable | Client IP address |
| `userAgent` | String | Nullable | Client browser/OS info |
| `createdAt` | DateTime | Auto-set | Event timestamp |

## Relationships

- **User → AuditLog**: One-to-many (a user has many audit log entries)
- **AuditLog → User**: Many-to-one (nullable — failed login attempts for non-existent users have no associated User)

## State Transitions

### User.status

```
[active] ───(5 failed logins)───→ [locked]
[locked]  ───(15 min elapsed)───→ [active] (auto, on next login attempt)
```

### Login Flow State

```
User submits credentials
    → Validate input (Zod schema)
        → Fail: Return error, preserve username field
        → Pass: Check lockout status
            → Locked: Return "Account locked" message
            → Not locked: Verify password
                → Invalid: Increment fail count, return generic error
                → Valid (5+ failures): Reset fail count, proceed
                → Valid (<5 failures): Reset fail count, proceed
                    → Issue JWT Cookie
                    → Write AuditLog (success)
                    → Redirect to /console
```

## Validation Rules (from spec)

| Rule | Field | Validation |
|------|-------|-----------|
| Username uniqueness | username | No existing user with same username (case-insensitive) |
| Password strength | passwordHash | 8-32 chars; at least 1 letter + 1 number + 1 special character; hashed with bcrypt cost ≥ 12 |
| Password match | confirmPassword | Must equal password field |
| Email format | email | Valid RFC 5322 email format |
| Username format | username | 3-32 characters; no HTML/JS/SQL injection characters |
| Rate limit | IP address | ≤ 10 login attempts per IP per minute |
| Account lock | username | ≤ 5 consecutive failed attempts; 15-minute lockout |
