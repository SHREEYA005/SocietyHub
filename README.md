# SocietyHub

A maintenance-complaint tracker for residential apartment societies.
Residents raise complaints with photos and track them to resolution;
admins triage by category/status/priority/date, catch overdue issues
before residents have to chase them, and keep everyone informed through
a pinned notice board and automatic email updates.

**Live app:** https://society-hub-iota.vercel.app
**Live API:** https://societyhub-backend-1rn8.onrender.com (docs at `/docs`)
**Repository:** https://github.com/SHREEYA005/SocietyHub

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

Vercel (React/TS) ──HTTPS/JSON──▶ Render (FastAPI, JWT-authenticated REST API)
│
├── SQLAlchemy ORM ──▶ Render PostgreSQL
├── local disk storage (uploads/)
└── SMTP email (or console log if unconfigured)


See `docs/system-design.md` for the reasoning behind the complaint
history model, overdue detection, photo handling, and notification flow.

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, React Router — deployed on Vercel
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0 — deployed on Render
- **Database**: PostgreSQL (Render managed instance) in production; SQLite for local dev
- **Auth**: JWT (python-jose) + bcrypt password hashing (passlib)
- **Tests**: pytest + FastAPI's `TestClient`

## Project Structure

society-maintenance-tracker/
├── backend/
│ ├── app/
│ │ ├── main.py # app entrypoint, CORS, error handlers
│ │ ├── config.py # env-driven settings
│ │ ├── database.py # SQLAlchemy engine/session
│ │ ├── models.py # User, Complaint, ComplaintHistory, Notice
│ │ ├── schemas.py # Pydantic request/response models
│ │ ├── auth.py / deps.py # JWT + auth dependencies
│ │ ├── routers/ # auth, complaints, admin, notices
│ │ ├── services/ # overdue.py, storage.py, email_service.py
│ │ └── seed.py # demo data
│ ├── tests/ # pytest suite
│ ├── requirements.txt
│ ├── runtime.txt # pins Python 3.12.10 for Render
│ └── .env.example
├── frontend/
│ ├── src/
│ │ ├── pages/ # Login, Register, dashboards, complaint pages...
│ │ ├── components/ # Navbar, StatusBadge, PriorityBadge, Timeline...
│ │ └── lib/ # api client, types, AuthContext
│ ├── vercel.json # SPA rewrite rule for client-side routing
│ ├── package.json
│ └── .env.example
├── docs/
│ ├── system-design.md # ≤800 words, required design write-up
│ ├── api-documentation.md
│ └── database-schema.md # includes Mermaid ER diagram
└── README.md


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
Interactive Swagger UI (live): https://societyhub-backend-1rn8.onrender.com/docs

## Environment Variables

Backend (`backend/.env.example`): `DATABASE_URL`, `JWT_SECRET`,
`OVERDUE_THRESHOLD_DAYS`, `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`,
`ALLOWED_IMAGE_TYPES`, `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USERNAME`/
`EMAIL_PASSWORD`/`EMAIL_FROM`/`EMAIL_USE_TLS`, `CORS_ORIGINS`,
`PYTHON_VERSION` (set to `3.12.10` on Render).

Frontend (`frontend/.env.example`): `VITE_API_URL`.

## Local Setup

### Prerequisites
- Python 3.12+
- Node.js 18+

### Running Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
python -m app.seed          # creates tables + demo data (SQLite by default)
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

Live app: https://society-hub-iota.vercel.app

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@societyhub.dev` | `AdminPass123!` |
| Resident | `arjun.mehta@societyhub.dev` | `ResidentPass123!` |
| Resident | `kavya.iyer@societyhub.dev` | `ResidentPass123!` |
| Resident | `rahul.sharma@societyhub.dev` | `ResidentPass123!` |

## Deployment

This app is deployed and live:

- **Backend**: Render Web Service (`societyhub-backend`), Python 3.12.10,
  root directory `backend/`, connected to a Render-managed PostgreSQL
  instance via `DATABASE_URL`. Build: `pip install -r requirements.txt`.
  Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Database**: Render PostgreSQL (`societyhub-db`), same region as the
  backend (Oregon) so the internal connection string resolves.
- **Frontend**: Vercel project (`society-hub`), root directory
  `frontend/`, framework preset Vite, `VITE_API_URL` pointed at the
  Render backend URL. `frontend/vercel.json` adds a SPA rewrite rule
  (`/(.*)` → `/index.html`) so client-side routes like `/dashboard`
  don't 404 on direct load/refresh.
- **CORS**: the backend's `CORS_ORIGINS` env var is set to the exact
  Vercel production URL (no trailing slash).

To redeploy from scratch, see the Local Setup instructions above and
mirror the same env vars into Render/Vercel's environment settings.

## Architecture Decisions

- **Postgres in production, SQLite for local dev** — one env var
  (`DATABASE_URL`) is the only difference; SQLAlchemy handles the rest.
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

See the live app at https://society-hub-iota.vercel.app (demo
credentials above) for the resident dashboard, complaint
detail/timeline, admin dashboard, and complaint management table.