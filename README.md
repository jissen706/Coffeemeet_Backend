# CoffeeMeet — Backend

REST API for CoffeeMeet, a lightweight coffee-chat scheduling platform built for organizations. Handles three user roles, slot management, booking logic, and transactional email.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **FastAPI** | Async-capable, automatic OpenAPI docs, Pydantic validation built in |
| ORM | **SQLAlchemy 2.0** | Declarative models, relationship management, session lifecycle |
| Database | **PostgreSQL** (Railway) | Production; SQLite works locally for dev |
| Auth | **python-jose** (JWT HS256) | Stateless tokens, role claims in payload, 30-day expiry |
| Password hashing | **argon2-cffi** | Industry-best password hashing for owner accounts |
| Email | **Brevo** (`sib-api-v3-sdk`) | Transactional email with .ics calendar attachment support |
| Deployment | **Railway** | Auto-deploy from `main`, managed Postgres, env vars |

---

## User Roles

```
Owner (admin)  → creates and manages cafes, baristas, customers, and slots
Barista (host) → joins a cafe via join_code, creates and manages their own slots
Customer       → joins via participant_code, books one slot per cafe
```

Roles are embedded in JWT tokens. Every protected endpoint checks `role` before allowing access.

---

## Project Structure

```
cofeeMeet/
├── main.py              # App factory, CORS, idempotent migrations
├── database.py          # SQLAlchemy engine + session
├── models.py            # ORM models (Cafe, Slot, Owner, Barista, Customer)
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # JWT creation, decoding, role-guard dependencies
├── email_service.py     # Brevo email builder + sender (booking/cancel/update)
├── seed.py              # Dev seed script
├── requirements.txt
├── railway.toml         # Railway deploy config
├── Procfile             # uvicorn start command
├── routers/
│   ├── owners.py        # POST /owners, POST /owners/login
│   ├── cafes.py         # Cafe CRUD, slot listing, host-slots, export
│   ├── baristas.py      # Barista register/login, delete
│   ├── customers.py     # Customer register/lookup, delete
│   └── slots.py         # Slot create, book, unbook, edit, delete, meet-link
└── tests/               # pytest integration tests
```

---

## Data Model

```
Owner
 └── Cafe (1:many)
      ├── join_code        (host-only, never returned on public endpoints)
      ├── participant_code (public)
      ├── one_slot         (bool: limit participants to one booking per cafe)
      ├── Barista (1:many, cascade delete)
      │    └── Slot (1:many, cascade delete)
      │         ├── start_time / end_time
      │         ├── location
      │         ├── meet_link  (optional, http/https validated)
      │         ├── status     (open | booked)
      │         └── customer_id → Customer (nullable)
      └── Customer (1:many, cascade delete)
```

**Key uniqueness constraints:**
- `barista.email` is unique per cafe
- `customer.email` is unique per cafe
- `cafe.join_code` and `cafe.participant_code` are globally unique

---

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/owners` | — | Register owner |
| POST | `/owners/login` | — | Owner login |
| POST | `/baristas` | — | Host register or login (requires `join_code`) |
| POST | `/customers/{cafe_id}` | — | Participant register or login |
| POST | `/customers/lookup/{cafe_id}` | — | Email-only lookup for returning participants |

### Cafes
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/cafes/join/{code}` | — | Load cafe by participant code (public — no `join_code` returned) |
| GET | `/cafes/host-join/{code}` | — | Load cafe by host code |
| GET | `/cafes/{cafe_id}` | — | Get cafe by ID |
| POST | `/cafes` | owner | Create cafe |
| PUT | `/cafes/{cafe_id}` | owner | Update cafe |
| GET | `/cafes/{cafe_id}/slots` | — | Public slot listing (customer name only, no email) |
| GET | `/cafes/{cafe_id}/host-slots` | barista/owner | Slot listing with full customer data incl. email |
| GET | `/cafes/{cafe_id}/baristas` | — | List hosts |
| GET | `/cafes/{cafe_id}/customers` | owner | List participants |
| GET | `/cafes/{cafe_id}/export` | owner | CSV export |

### Slots
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/slots` | barista/owner | Create slot |
| PUT | `/slots/{id}/book` | — | Book a slot |
| PATCH | `/slots/{id}/unbook` | any role | Cancel a booking |
| PATCH | `/slots/{id}/edit` | barista/owner | Edit location or meet link |
| PATCH | `/slots/{id}/meet-link` | barista/owner | Set meet link on a booked slot |
| DELETE | `/slots/{id}` | barista/owner | Delete slot |

### Admin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/owners/{id}/cafes` | owner | List owner's cafes |
| DELETE | `/baristas/{id}` | owner | Remove host (cascades slots) |
| DELETE | `/customers/{id}` | owner | Remove participant (slots reopen, meet links preserved) |

---

## Security Design

**Separate join codes.** Each cafe has two distinct random 6-character codes: `join_code` (host-only) and `participant_code` (public). Participants cannot find the host code — `join_code` is excluded from all public-facing responses via the `PublicCafeResponse` schema.

**Role-based JWT.** Every token embeds `role`, `sub` (user ID), and `cafe_id`. Endpoints verify both role and ownership — a barista can only modify their own slots; an owner can only modify cafes they own.

**SELECT FOR UPDATE on booking.** The slot booking endpoint uses a row-level lock to prevent the double-booking race condition under concurrent load.

**meet_link validation.** All virtual meeting link fields reject anything not starting with `http://` or `https://`, blocking `javascript:` and `data:` URI XSS vectors from appearing in emails.

**Customer email privacy.** The public `/cafes/{id}/slots` endpoint uses `SlotCustomerResponse` (name only, no email). Customer emails are only returned through the authenticated `/cafes/{id}/host-slots` endpoint available to verified hosts and owners.

**Password hashing.** Owner passwords are hashed with Argon2 (argon2-cffi). Hosts and participants are passwordless — they authenticate via their cafe's join code and email identity, appropriate for the low-friction use case.

---

## Email System

Three transactional emails are sent via Brevo:

| Trigger | Email | Attachment |
|---------|-------|------------|
| Slot booked | Booking confirmation with slot details | `.ics` calendar invite |
| Booking cancelled by host/owner | Cancellation notice with rebook link | — |
| Slot edited (location or meet link changed) | Update notice with new details | — |

All email buttons link to `/booking/{participant_code}` — a dedicated page where the participant enters their email to restore their session without requiring a password. No personal data is embedded in link URLs.

Emails are fired in background daemon threads so they never block the API response.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | JWT signing secret — generate with `openssl rand -hex 32` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins (e.g. `https://yourapp.vercel.app`) |
| `BREVO_API_KEY` | Yes | Brevo REST API key (starts with `xkeysib-`, not `xsmtpsib-`) |
| `EMAIL_ADDRESS` | Yes | Verified sender address in Brevo |
| `FRONTEND_URL` | Yes | Base URL of the frontend deployment |

---

## Local Development

```bash
# 1. Clone and create virtualenv
python -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export SECRET_KEY="dev-secret"
export DATABASE_URL="sqlite:///./cafe.db"
export CORS_ORIGINS="http://localhost:5173"

# 4. Run
uvicorn main:app --reload

# 5. Run tests
pytest
```

Interactive API docs at `http://localhost:8000/docs`.

---

## Deployment (Railway)

1. Connect your GitHub repo to a Railway project
2. Add a PostgreSQL plugin — Railway injects `DATABASE_URL` automatically
3. Set all required environment variables in Railway dashboard
4. Push to `main` — Railway auto-deploys via `railway.toml` and `Procfile`

---

*Built by Penn Engineering Student.*
