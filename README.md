# SocietyHub

A maintenance-complaint tracker for residential apartment societies.
Residents raise complaints with photos and track them to resolution;
admins triage by category/status/priority/date, catch overdue issues
before residents have to chase them, and keep everyone informed through
a pinned notice board and automatic email updates.

## Product Overview

Two roles, two focused experiences:

- **Resident** — register/login, raise a complaint (category,
  description, optional photo), see all their own complaints with a
  full status timeline, read the notice board, get emailed when a
  complaint updates or an important notice goes up.
- **Admin** — see every complaint with search/filter (category, status,
  priority, date, overdue), move a complaint through
  `OPEN → IN_PROGRESS → RESOLVED`, set priority, add a note on every
  change, post notices (optionally pinned + emailed), and read a
  dashboard with status/category/priority breakdowns and an overdue
  count.

## Key Features

- Full complaint lifecycle with an **append-only audit trail** (every
  status/priority change is a new row, never edited)
- **Configurable overdue detection** (`OVERDUE_THRESHOLD_DAYS`),
  computed live rather than stored, so resolved complaints are never
  stuck "overdue" and threshold changes apply instantly
- Human-readable **SLA messaging** ("Due in 18 hours" / "Overdue by 2 days")
- Deliberate, note-required **reopen** flow instead of silently allowing
  `RESOLVED → OPEN`
- Secure photo upload: type/size validation, server-generated filenames
  (original filename never trusted)
- Notice board with pinned important notices + resident email fan-out
- Admin dashboard: totals by status/category/priority, overdue +
  high-priority-overdue counts
- Ownership enforced server-side — a resident cannot fetch another
  resident's complaint by guessing an ID
- Human-friendly complaint reference codes (`SMT-2026-4F2A9C`)
- 19 backend tests covering auth, ownership, transitions, overdue logic, notices

## Architecture

```
Browser (React/TS) ──HTTP/JSON──▶ FastAPI (JWT-authenticated REST API)
                                        │
                                        ├── SQLAlchemy ORM ──▶ SQLite (dev) / PostgreSQL (prod)
                                        ├── local disk storage (uploads/, swappable)
                                        └── SMTP email (or console log if unconfigured)
```

See `docs/system-design.md` for the reasoning behind the complaint
history model, overdue detection, photo handling, and notification flow.

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, React Router — no CSS
  framework, hand-written CSS for a small, controllable bundle
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0
- **Database**: SQLite by default (zero setup); PostgreSQL via
  `DATABASE_URL` in production
- **Auth**: JWT (python-jose) + bcrypt password hashing (passlib)
- **Tests**: pytest + FastAPI's `TestClient`

## Project Structure

```
society-maintenance-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py            # app entrypoint, CORS, error handlers
│   │   ├── config.py          # env-driven settings
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # User, Complaint, ComplaintHistory, Notice
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── auth.py / deps.py  # JWT + auth dependencies
│   │   ├── routers/           # auth, complaints, admin, notices
│   │   ├── services/          # overdue.py, storage.py, email_service.py
│   │   └── seed.py            # demo data
│   ├── tests/                 # pytest suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/              # Login, Register, dashboards, complaint pages...
│   │   ├── components/         # Navbar, StatusBadge, PriorityBadge, Timeline...
│   │   └── lib/                # api client, types, AuthContext
│   ├── package.json
│   └── .env.example
├── docs/
│   ├── system-design.md        # ≤800 words, required design write-up
│   ├── api-documentation.md
│   └── database-schema.md      # includes Mermaid ER diagram
└── README.md
```

## Database Schema

See `docs/database-schema.md` for the full ER diagram and design notes.

## Authentication

JWT bearer tokens, issued on register/login, expiring after
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h). Role (`resident`/`admin`)
is embedded in the token and re-checked server-side on every protected
route — the frontend hiding admin links is a UX convenience, not the
security boundary. There is no public admin-signup endpoint; the seeded
admin account is created by `app/seed.py` (see Demo Credentials below).

## API Documentation

Full endpoint-by-endpoint reference: `docs/api-documentation.md`.
Interactive Swagger UI: `http://localhost:8000/docs` while the backend is running.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example`
to `frontend/.env`, then fill in as needed. Nothing in `.env.example`
contains real secrets.

Backend (`backend/.env.example`): `DATABASE_URL`, `JWT_SECRET`,
`OVERDUE_THRESHOLD_DAYS`, `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`,
`ALLOWED_IMAGE_TYPES`, `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USERNAME`/
`EMAIL_PASSWORD`/`EMAIL_FROM`/`EMAIL_USE_TLS`, `CORS_ORIGINS`.

Frontend (`frontend/.env.example`): `VITE_API_URL`.

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+

### Database Setup
No setup needed for local dev — SQLite is used by default and the file
is created automatically on first run. For Postgres, create a database
and point `DATABASE_URL` at it (SQLAlchemy handles the rest).

### Running Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed          # creates tables + demo data
uvicorn app.main:app --reload --port 8000
```
Backend is now at `http://localhost:8000` (docs at `/docs`).

### Running Frontend
```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_URL=http://localhost:8000
npm run dev
```
Frontend is now at `http://localhost:5173`.

### Running Tests
```bash
cd backend
pip install -r requirements.txt   # includes pytest + httpx
pytest -v
```
19 tests covering registration/login, ownership isolation, admin-only
enforcement, status transitions (valid and invalid), reopen, priority
changes + history, overdue detection (including "resolved is never
overdue"), empty-list states, and invalid photo uploads.

## Seed Data

`python -m app.seed` (re-runnable — it resets the DB each time) creates
one admin, three residents, six complaints spanning every status and
priority (including overdue examples with backdated timestamps and full
history), and four notices (two marked important).

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@societyhub.dev` | `AdminPass123!` |
| Resident | `arjun.mehta@societyhub.dev` | `ResidentPass123!` |
| Resident | `kavya.iyer@societyhub.dev` | `ResidentPass123!` |
| Resident | `rahul.sharma@societyhub.dev` | `ResidentPass123!` |

## Deployment

This repository is **not deployed** by default — no real database,
SMTP, or hosting credentials exist in this environment. To deploy it
yourself:

1. **Backend** → Render or Railway (free tier):
   - New Web Service from this repo, root `backend/`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add a managed Postgres instance on the same platform, set
     `DATABASE_URL` to its connection string
   - Set `JWT_SECRET` (long random value), `CORS_ORIGINS` to your
     deployed frontend URL, and SMTP vars if you want real email
2. **Frontend** → Vercel or Netlify:
   - Root `frontend/`, build `npm run build`, output `dist/`
   - Set `VITE_API_URL` to your deployed backend URL
3. Run `python -m app.seed` once against the production database (via a
   one-off shell on the host, or a temporary local connection) to load
   demo data, or register fresh accounts through the UI.

## Architecture Decisions

- **SQLite by default, Postgres via one env var** — zero-friction local
  evaluation without sacrificing a real production path.
- **Overdue computed, not stored** — see `docs/system-design.md`.
- **Reopen is a separate endpoint, not a free status transition** — an
  intentional, auditable action rather than an accidental one.
- **404, not 403, on cross-resident access** — avoids confirming a
  complaint ID exists to someone who shouldn't see it.
- **Email degrades to logging, never blocks** — the app is fully
  functional and testable without SMTP credentials, and a notification
  failure never rolls back the underlying status change.

## Security Considerations

- Passwords hashed with bcrypt, never stored or logged in plaintext
- JWT-based auth; role re-checked server-side on every protected route
- File uploads validated by content-type and size; filenames are
  server-generated, never derived from client input
- CORS origins are explicit and configurable, not wildcarded
- No secrets committed — `.env` is git-ignored, only `.env.example` is tracked
- Generic error messages returned to clients; full errors only logged server-side

## Future Improvements

- Push/in-app notifications alongside email
- Bulk admin actions (assign multiple complaints at once)
- Per-category configurable overdue thresholds
- Resident-facing complaint comments (not just admin notes)
- Rate limiting on auth endpoints

## Screenshots

Not included in this submission — run the app locally (see Local Setup
above) to view the resident dashboard, complaint detail/timeline, admin
dashboard, and complaint management table directly.
