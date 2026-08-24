# SocietyHub — API Documentation

Base URL (local): `http://localhost:8000`
Interactive Swagger UI is also available at `/docs` (and ReDoc at `/redoc`)
whenever the backend is running.

All authenticated endpoints require `Authorization: Bearer <token>`.
Errors follow a consistent shape: `{ "detail": "human readable message" }`.

## Authentication

### `POST /auth/register`
Registers a new **resident** account (admin accounts are not
self-service; see README for how the seeded admin is created).
- Auth: none
- Request: `{ name, email, password, flat_number? }`
- Response `201`: `{ access_token, token_type, user }`
- Errors: `409` email already registered, `422` invalid payload

### `POST /auth/login`
- Auth: none
- Request: `{ email, password }`
- Response `200`: `{ access_token, token_type, user }`
- Errors: `401` incorrect email or password

### `GET /auth/me`
- Auth: required
- Response `200`: current user object

## Complaints

### `POST /complaints`
Create a complaint (resident only, via their own token). `multipart/form-data`.
- Fields: `category`, `description`, `photo` (optional file)
- Response `201`: complaint with initial `CREATED` history entry
- Errors: `400` invalid/oversized/wrong-type photo, `422` invalid fields

### `GET /complaints`
List the current resident's own complaints. Optional `?status_filter=OPEN|IN_PROGRESS|RESOLVED`.
- Response `200`: array of complaints (own only)

### `GET /complaints/{id}`
Fetch one complaint with its full history.
- Errors: `404` if not found **or** not owned by the caller (residents
  cannot distinguish "doesn't exist" from "not yours")

### `GET /complaints/{id}/history`
Returns just the history array for a complaint (same ownership rule as above).

### `PATCH /complaints/{id}/status` (admin only)
- Request: `{ status: "OPEN"|"IN_PROGRESS"|"RESOLVED", note? }`
- Errors: `400` same-status or invalid transition (e.g. `RESOLVED → IN_PROGRESS`), `403` non-admin, `404` not found
- Side effect: sends a status-change email to the resident (logged if SMTP isn't configured)

### `PATCH /complaints/{id}/reopen` (admin only)
Moves a `RESOLVED` complaint back to `OPEN`. Requires a non-empty `note`.
- Request: `{ status: "OPEN", note }`
- Errors: `400` complaint isn't resolved, or note missing

### `PATCH /complaints/{id}/priority` (admin only)
- Request: `{ priority: "LOW"|"MEDIUM"|"HIGH", note? }`
- Errors: `400` already at that priority

## Admin

### `GET /admin/complaints` (admin only)
Query params (all optional, combinable): `category`, `status`,
`priority`, `overdue_only=true`, `date_from`, `date_to` (YYYY-MM-DD),
`search` (matches reference code or description).
Results are sorted overdue-first, then by priority (HIGH → LOW), then newest first.

### `GET /admin/dashboard` (admin only)
Response:
```json
{
  "total_complaints": 12, "open_count": 4, "in_progress_count": 3,
  "resolved_count": 5, "overdue_count": 2, "overdue_high_priority_count": 1,
  "by_category": { "Plumbing": 5, "Electrical": 3 },
  "by_priority": { "LOW": 2, "MEDIUM": 6, "HIGH": 4 },
  "overdue_threshold_days": 3
}
```

## Notices

### `GET /notices`
Any authenticated user. Important notices first, then newest first.

### `POST /notices` (admin only)
- Request: `{ title, content, is_important }`
- Side effect: if `is_important`, emails every resident.

## Static Files

Uploaded photos are served at `GET /uploads/<filename>`.

## HTTP Status Codes Used

| Code | Meaning |
|------|---------|
| 200/201 | success |
| 400 | validation/business-rule failure (bad transition, oversized file, duplicate priority, etc.) |
| 401 | missing/invalid/expired token, or bad login |
| 403 | authenticated but not authorized (e.g. resident hitting an admin route) |
| 404 | not found, or not yours (ownership hidden as not-found) |
| 422 | request body failed schema validation |
| 503 | database temporarily unavailable |
