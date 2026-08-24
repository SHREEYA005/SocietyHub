# SocietyHub — Database Schema

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : raises
    USERS ||--o{ COMPLAINT_HISTORY : "acted as"
    USERS ||--o{ NOTICES : authors
    COMPLAINTS ||--o{ COMPLAINT_HISTORY : has

    USERS {
        int id PK
        string name
        string email UK
        string hashed_password
        enum role "resident | admin"
        string flat_number "nullable"
        datetime created_at
    }

    COMPLAINTS {
        int id PK
        string reference_code UK "e.g. SMT-2026-4F2A9C"
        int resident_id FK
        string category
        text description
        string photo_path "nullable"
        enum status "OPEN | IN_PROGRESS | RESOLVED"
        enum priority "LOW | MEDIUM | HIGH"
        datetime created_at
        datetime updated_at
        datetime resolved_at "nullable"
    }

    COMPLAINT_HISTORY {
        int id PK
        int complaint_id FK
        enum event_type "CREATED | STATUS_CHANGE | PRIORITY_CHANGE"
        enum previous_status "nullable"
        enum new_status "nullable"
        enum previous_priority "nullable"
        enum new_priority "nullable"
        text note "nullable"
        int actor_id FK
        string actor_name "denormalized snapshot"
        datetime created_at
    }

    NOTICES {
        int id PK
        string title
        text content
        boolean is_important
        int author_id FK
        string author_name
        datetime created_at
    }
```

## Design Notes

- **Normalization**: structured facts (status, priority, category) are
  real columns with enum constraints, not packed into free text — this
  is what makes filtering/dashboard aggregation reliable and fast.
- **`complaint_history` is append-only**: no endpoint updates or deletes
  a row. It is the audit trail for the complaint lifecycle.
- **`reference_code`** is a unique, human-friendly identifier
  (`SMT-<year>-<6 hex chars>`) shown throughout the UI instead of the
  raw numeric primary key.
- **Cascading deletes**: `complaints.resident_id` and
  `complaint_history.complaint_id` use `ON DELETE CASCADE` so orphaned
  rows can't accumulate if a user or complaint is ever removed.
- **Indexes**: `users.email` (unique), `complaints.reference_code`
  (unique), and `complaints.status` / `.category` / `.priority` /
  `.created_at` are indexed since they're the primary filter/sort
  targets on the admin complaints view.
- **Overdue is not a column** — see `docs/system-design.md` §2 for why
  it's computed on read instead of stored.
- **Configuration** (`OVERDUE_THRESHOLD_DAYS`, email/storage settings)
  lives in environment variables (`app/config.py`), not a database
  table — it's deployment-time configuration, not application data.
