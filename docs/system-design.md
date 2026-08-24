# SocietyHub — System Design

## 1. Complaint History Model

Every complaint has an append-only `complaint_history` table, never an
`UPDATE`/`DELETE` operation exposed through the API. Each row records
`event_type` (`CREATED`, `STATUS_CHANGE`, `PRIORITY_CHANGE`), the
previous and new values, the `actor_id`/`actor_name` (a denormalized
snapshot of who performed it), an optional `note`, and a timestamp.

This design was chosen over storing "current status + last note" on the
complaint row itself because the assignment explicitly requires a full,
tamper-evident audit trail — a ticketing-style history, not just a
mutable status field. Denormalizing `actor_name` at write time means the
timeline still reads correctly even if a user's name changes later.

The complaint lifecycle is a small explicit state machine: `OPEN →
IN_PROGRESS → RESOLVED`, with `OPEN ⇄ IN_PROGRESS` both ways (an admin
can move a complaint back to `IN_PROGRESS` from `OPEN` and vice versa as
work starts/pauses). `RESOLVED` is terminal for the normal status-update
endpoint — arbitrary transitions out of `RESOLVED` are rejected. Re-
opening a resolved complaint is deliberately a *different* endpoint
(`PATCH /complaints/{id}/reopen`) that requires a note, so it is always
distinguishable in the audit trail from a routine transition, and can't
happen by a stray click. Every transition — including reopening and
priority changes — writes a new history row; nothing is ever edited.

## 2. Overdue Detection

The threshold is fully configurable via `OVERDUE_THRESHOLD_DAYS` (an
environment variable, defaulting to 3), not hardcoded. Rather than
storing an `is_overdue` boolean column that would need to be kept in
sync with a changing threshold and the passage of time, overdue status
is **computed on read**: `now - created_at >= threshold_days`, and only
for complaints that are not `RESOLVED`. This guarantees a resolved
complaint can never show as overdue, and that changing the threshold
takes effect immediately across the whole system without a migration or
background job. The same computation also powers the human-readable SLA
line ("Due in 18 hours" / "Overdue by 2 days") shown on both the
resident and admin views, and admin listings are sorted so overdue,
high-priority complaints surface first.

## 3. Photo Handling

Photos are optional and validated on three axes: MIME type (allow-list:
JPEG/PNG/WebP), size (`MAX_UPLOAD_SIZE_MB`, default 5MB), and non-empty
content. The client-supplied filename is never trusted or used for
storage — a fresh UUID-based filename is generated server-side, with the
extension derived from the validated content type, not from the
original name. Files are persisted through a small storage abstraction
(`app/services/storage.py`) with a single `save_complaint_photo()`
entry point; today it writes to local disk under `UPLOAD_DIR` and is
served via a static mount, but the interface is narrow enough to swap
in S3/Cloudinary later without touching the router or model layer.
Upload failures (disk error, invalid type, oversized file) return a
clear 400/500 with a specific message rather than a raw stack trace,
and never partially create a complaint record.

## 4. Notification Flow

Two triggers send email: a complaint status change (to that complaint's
resident) and publishing an *important* notice (to all residents). Both
go through `app/services/email_service.py`, which uses `smtplib`
against configured SMTP settings. Critically, if `EMAIL_HOST` is unset,
the service logs the email instead of failing — this lets the full
application run and be evaluated without real email credentials, while
the send path itself is genuinely implemented and takes effect the
moment credentials are supplied. Email sending is wrapped so that a
failure (bad credentials, provider outage) is logged and swallowed
rather than rolling back or failing the triggering request — a resident
should never lose a status update because a notification email bounced.

## Why This Architecture

FastAPI + SQLAlchemy + Pydantic gives typed request/response validation,
automatic OpenAPI docs, and a small enough dependency surface to satisfy
the "minimal dependencies" constraint while remaining production-
realistic. SQLite is used by default for zero-setup local evaluation;
`DATABASE_URL` is the only thing that needs to change to point at
Postgres in production — no code changes, since SQLAlchemy abstracts the
dialect. JWT-based auth keeps the API stateless and easy to deploy
behind any load balancer. Authorization is enforced server-side on
every complaint-scoped endpoint (a resident querying another resident's
complaint ID gets a 404, not a 403, to avoid confirming the ID exists),
never relying on the frontend to hide UI.
