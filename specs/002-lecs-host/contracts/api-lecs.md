# API Contracts: LECS Host Management v1

## Standard Response Format

All API v1 endpoints return responses in this format:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Human-readable error description",
    "details": { "fieldName": ["error message", ...] }
  }
}
```

---

## GET /api/v1/lecs-hosts

Query active host list with pagination and optional status filter.

### Request

**Query Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `page` | Integer | No | Page number (default: 1) |
| `pageSize` | Integer | No | Items per page (default: 20, max: 100) |
| `status` | String[] | No | Filter by status (comma-separated: `normal,stopped,failed`) |
| `billingMode` | String | No | Filter by billing mode (`PREPAID` or `PAY_AS_YOU_GO`) |

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <service-token>` or `Cookie: auth_token=<jwt>` |

### Response

**200 OK**:

```json
{
  "success": true,
  "data": {
    "hosts": [
      {
        "id": "uuid",
        "hostname": "host-01",
        "billingMode": "PREPAID",
        "status": "normal",
        "instanceType": "2vCPU+4GiB",
        "privateIp": "192.168.1.10",
        "createdAt": "2026-05-10T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 150,
      "totalPages": 8
    }
  },
  "error": null
}
```

**401 Unauthorized** — Invalid or missing authentication token.

---

## POST /api/v1/lecs-hosts

Submit a new LECS host creation request.

### Request

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <service-token>` or `Cookie: auth_token=<jwt>` |
| `Content-Type` | Yes | `application/json` |

**Body** (`application/json`):

```json
{
  "billingMode": "PREPAID",
  "hostname": "my-host-01",
  "credentialUsername": "admin_user",
  "credentialPassword": "P@ssw0rd!234",
  "instanceType": "ECONOMY",
  "instancePlan": "2vCPU+4GiB",
  "osImage": "EULER_OS",
  "ipAllocation": "DHCP",
  "purchaseMonths": 3
}
```

Or with manual IP:

```json
{
  "billingMode": "PREPAID",
  "hostname": "my-host-01",
  "credentialUsername": "admin_user",
  "credentialPassword": "P@ssw0rd!234",
  "instanceType": "HIGH_PERFORMANCE",
  "instancePlan": "4vCPU+8GiB",
  "osImage": "UBUNTU",
  "ipAllocation": "MANUAL",
  "ipAddress": "192.168.1.50",
  "subnetMask": 24,
  "purchaseMonths": 6
}
```

### Valid Instance Plans

**ECONOMY**: `2vCPU+2GiB`, `2vCPU+4GiB`, `2vCPU+8GiB`, `4vCPU+8GiB`
**HIGH_PERFORMANCE**: `2vCPU+4GiB`, `2vCPU+8GiB`, `4vCPU+8GiB`, `8vCPU+16GiB`

### Response

**201 Created** — Host creation accepted:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "hostname": "my-host-01",
    "status": "creating",
    "estimatedCost": {
      "amount": 420,
      "currency": "CNY",
      "unit": "total"
    },
    "createdAt": "2026-05-12T08:00:00Z"
  },
  "error": null
}
```

**400 Bad Request** — Validation errors:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Invalid input parameters",
    "details": {
      "hostname": ["Hostname must be 4-10 characters, cannot start with _"]
    }
  }
}
```

**403 Forbidden** — Quota exceeded:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "message": "Host count has reached the maximum limit of 100"
  }
}
```

---

## GET /api/v1/lecs-hosts/:id

Get details of a specific host.

### Response

**200 OK**:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "hostname": "my-host-01",
    "billingMode": "PREPAID",
    "status": "normal",
    "instanceType": "ECONOMY",
    "instancePlan": "2vCPU+4GiB",
    "osImage": "EULER_OS",
    "ipAllocation": "DHCP",
    "privateIp": "192.168.1.10",
    "createdAt": "2026-05-10T10:00:00Z",
    "startedAt": "2026-05-10T10:05:00Z",
    "costSnapshot": 14000
  },
  "error": null
}
```

**404 Not Found** — Host does not exist or is soft-deleted.

---

## POST /api/v1/lecs-hosts/:id/stop

Shutdown a running host.

### Request

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <service-token>` or `Cookie: auth_token=<jwt>` |

**Body**: Empty (no body required).

### Response

**202 Accepted** — Shutdown request queued:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "shutting_down"
  },
  "error": null
}
```

**403 Forbidden** — Host is not in "normal" state:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_STATE",
    "message": "Host is not in 'normal' state. Current state: stopped"
  }
}
```

---

## POST /api/v1/lecs-hosts/:id/start

Start a stopped or failed host.

### Request

Same as `/stop` — headers only, no body.

### Response

**202 Accepted** — Start request queued:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "starting"
  },
  "error": null
}
```

**403 Forbidden** — Host is not in "stopped" or "failed" state:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_STATE",
    "message": "Host is not in 'stopped' or 'failed' state. Current state: normal"
  }
}
```

---

## DELETE /api/v1/lecs-hosts/:id

Soft-delete a host. Only allowed for hosts in "stopped" or "failed" state.

### Request

**Headers**:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <service-token>` or `Cookie: auth_token=<jwt>` |

### Response

**202 Accepted** — Deletion request queued:

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "deleting"
  },
  "error": null
}
```

**403 Forbidden** — Host is not in deletable state:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_STATE",
    "message": "Please shut down the host before deleting"
  }
}
```
