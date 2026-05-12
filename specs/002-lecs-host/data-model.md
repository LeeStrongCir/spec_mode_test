# Data Model: LECS Host Management

## Entities

### LECsHost

A virtual compute instance owned by a user.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID (auto) | Primary Key | Unique internal identifier |
| `userId` | UUID (FK → User) | Not nullable, indexed | Owner of the host |
| `hostname` | String (4-10 chars) | Not nullable | Display name (`[a-zA-Z0-9_]{4,10}`, cannot start with `_`) |
| `billingMode` | Enum | `PREPAID` \| `PAY_AS_YOU_GO` | Not nullable |
| `credentialUsername` | String (4-16 chars) | Not nullable | Access username (stored in plain text for provisioning; encrypted at rest) |
| `credentialPasswordHash` | String | Not nullable | Hashed access credential |
| `instanceTypeId` | UUID (FK → InstanceType) | Not nullable | Chosen instance type |
| `osImage` | Enum | `EULER_OS` \| `UBUNTU` \| `WINDOWS` | Not nullable |
| `ipAllocation` | Enum | `DHCP` \| `MANUAL` | Not nullable |
| `ipAddress` | String (IPv4) | Nullable; required when `ipAllocation=MANUAL` | Manual IP address |
| `subnetMask` | Integer (8-24) | Nullable; required when `ipAllocation=MANUAL` | Subnet mask prefix length |
| `purchaseMonths` | Integer | Not nullable | Duration: 1-9 (months), 12 (1 year), 24 (2 years) |
| `costSnapshot` | Integer (cents) | Not nullable | Calculated cost at creation time |
| `privateIp` | String (IPv4) | Nullable; auto-assigned on creation success | Assigned private IP |
| `status` | Enum | See states below | Not nullable, indexed |
| `createdAt` | DateTime | Auto-set | Creation request timestamp |
| `startedAt` | DateTime | Nullable | Time host entered "Normal" state |
| `deletedAt` | DateTime | Nullable; auto-set on deletion completed | Soft-delete timestamp |

### InstanceType

Pre-defined compute configuration plan.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID (auto) | Primary Key | Unique internal identifier |
| `name` | String | Not nullable, unique | Display name (e.g., "2vCPU+4GiB") |
| `planType` | Enum | `ECONOMY` \| `HIGH_PERFORMANCE` | Not nullable, indexed |
| `vcpu` | Integer | Not nullable | Number of virtual CPUs |
| `memoryGiB` | Integer | Not nullable | Memory in GiB |
| `systemDiskGB` | Integer | Not nullable | System disk size (default 40GB) |
| `monthlyPriceCents` | Integer | Not nullable | Base monthly price in cents |

### AuditLog (extension of existing model)

New fields added for LECS operations:

| Field | Type | Constraints | Description |
|---|---|---|---|
| `resourceType` | Enum | `USER` \| `LECS_HOST` | Not nullable (new column) |
| `resourceId` | UUID | Nullable; references LECsHost or User | Target resource |
| `details` | JSON | Nullable | Operation-specific details (before/after state) |

## Relationships

- **User → LECsHost**: One-to-many (a user owns many hosts)
- **InstanceType → LECsHost**: One-to-many (a spec is referenced by many hosts)
- **LECsHost → AuditLog**: One-to-many (a host has many audit log entries)
- **User → AuditLog**: One-to-many (existing relationship, expanded with resourceType)

## State Machine

```
                     ┌──────────────┐
                     │   Creating   │  (async, max 30s)
                     └──────┬───────┘
                   success ↙│↘ failure/timeout
            ┌──────────┐    │    ┌───────────┐
            │  Normal  │    │    │  Failed   │
            └───┬─────┘    │    └────┬──────┘
         user stops ↘      │   user deletes ↗
                    ┌──────┴──────┐
                    │ ShuttingDown│  (async, ~10s)
                    └──────┬──────┘
                       ↓ completed
            ┌────────────┴────────┐
            │      Stopped        │
            │  ┌────────────────┐ │
            │  │     Failed     │ │
            │  └────────────────┘ │
            │  user deletes       │
            │  └────────┬────────┘
            │     ┌──────┴──────┐
            │     │  Deleting   │  (async, ~5s)
            │     └──────┬──────┘
            │          ↓ completed
            │     ┌──────┴──────┐
            │     │  Starting   │  (async, ~10s)
            │     └──────┬──────┘
            │          ↓ completed
            │     ┌──────┴──────┐
            │     │   Normal    │
            │     └─────────────┘
            └───────────────────┘
```

### State Transition Rules

| From State | Allowed Action | Next State | Notes |
|---|---|---|---|
| Creating | — | Normal / Failed | Terminal: reached via async job |
| Normal | stop | ShuttingDown | Only stop allowed |
| Normal | — | — | Delete not allowed |
| Failed | start | Starting | Only start/delete allowed |
| Failed | delete | Deleting | |
| ShuttingDown | — | Stopped | Terminal: reached via async job |
| Stopped | start | Starting | |
| Stopped | delete | Deleting | |
| Starting | — | Normal | Terminal: reached via async job |
| Deleting | — | (soft-deleted) | Terminal: `deletedAt` set |

### Button Enable/Disable Matrix

| State | Shutdown | Start | Delete |
|---|---|---|---|
| Creating | ❌ | ❌ | ❌ |
| Normal | ✅ | ❌ | ❌ |
| Failed | ❌ | ✅ | ✅ |
| ShuttingDown | ❌ | ❌ | ❌ |
| Stopped | ❌ | ✅ | ✅ |
| Starting | ❌ | ❌ | ❌ |
| Deleting | ❌ | ❌ | ❌ |

## Validation Rules (from spec)

| Rule | Field | Validation |
|---|---|---|
| Hostname format | hostname | 4-10 chars, `[a-zA-Z0-9_]`, cannot start with `_` |
| Credential username | credentialUsername | 4-16 chars, `[a-zA-Z0-9!@#$%^&*()-=+]` |
| Credential password | credentialPasswordHash | 8-32 chars, complexity validated before hashing |
| Instance type | instanceTypeId | Must be a valid FK reference |
| OS image | osImage | Enum: EULER_OS, UBUNTU, WINDOWS |
| IP allocation | ipAllocation | Enum: DHCP or MANUAL |
| Manual IP | ipAddress | Valid IPv4 format (regex) |
| Subnet mask | subnetMask | Integer 8-24 |
| Purchase months | purchaseMonths | 1-9, 12, or 24 |
| Quota limit | userId + COUNT(deletedAt IS NULL) | Max 100 active hosts per user |
