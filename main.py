import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import engine, Base
import models
from routers import owners, baristas, customers, slots, cafes

load_dotenv()

Base.metadata.create_all(bind=engine)

# Idempotent migrations — Postgres-only statements are skipped on SQLite (tests).
# Wrapped in a broad try/except so a migration hiccup never blocks app startup
# (Railway marks the deploy as failed if uvicorn can't import this module).
import logging as _logging
from sqlalchemy import text, inspect

_log = _logging.getLogger("startup-migrations")

def _exec(stmt: str, label: str) -> None:
    """Run a single migration statement in its own transaction. A failure of
    one statement must not poison the next — Postgres aborts the entire
    transaction on the first error inside it."""
    try:
        with engine.begin() as conn:
            conn.execute(text(stmt))
    except Exception as e:
        _log.warning("Skipping migration %s: %s", label, e)


def _run_startup_migrations():
    dialect = engine.dialect.name  # 'postgresql', 'sqlite', etc.

    if dialect == "postgresql":
        _exec("ALTER TABLE baristas ADD COLUMN IF NOT EXISTS bio TEXT", "baristas.bio")
        _exec("ALTER TABLE cafes ADD COLUMN IF NOT EXISTS participant_code VARCHAR", "cafes.participant_code")
        _exec("ALTER TABLE slots ADD COLUMN IF NOT EXISTS notes TEXT", "slots.notes")
        _exec("ALTER TABLE cafes ADD COLUMN IF NOT EXISTS description TEXT", "cafes.description")
        _exec("ALTER TABLE cafes ADD COLUMN IF NOT EXISTS max_participants INTEGER NOT NULL DEFAULT 1", "cafes.max_participants")
        _exec(
            """
            UPDATE cafes
            SET participant_code = UPPER(SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 6))
            WHERE participant_code IS NULL
            """,
            "participant_code backfill",
        )
        _exec(
            """
            UPDATE cafes c
            SET participant_code = UPPER(SUBSTRING(MD5(c.id::TEXT || 'p') FROM 1 FOR 6))
            WHERE participant_code IN (
                SELECT participant_code FROM cafes GROUP BY participant_code HAVING COUNT(*) > 1
            )
            """,
            "participant_code dedup",
        )

    # Backfill bookings junction table from legacy slots.customer_id, if that
    # column still exists. Filter to only customer ids that actually exist so a
    # stale FK in the legacy column can't break the insert.
    try:
        inspector = inspect(engine)
        if inspector.has_table("slots") and inspector.has_table("slot_bookings"):
            slot_cols = {c["name"] for c in inspector.get_columns("slots")}
            if "customer_id" in slot_cols:
                _exec(
                    """
                    INSERT INTO slot_bookings (slot_id, customer_id, created_at)
                    SELECT s.id, s.customer_id, CURRENT_TIMESTAMP
                    FROM slots s
                    WHERE s.customer_id IS NOT NULL
                      AND EXISTS (SELECT 1 FROM customers c WHERE c.id = s.customer_id)
                      AND NOT EXISTS (
                          SELECT 1 FROM slot_bookings b
                          WHERE b.slot_id = s.id AND b.customer_id = s.customer_id
                      )
                    """,
                    "slot_bookings backfill",
                )
    except Exception as e:
        _log.warning("inspect-based migration step skipped: %s", e)

try:
    _run_startup_migrations()
except Exception as _e:
    _log.exception("startup migrations crashed but app will continue: %s", _e)

_raw_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(owners.router)
app.include_router(baristas.router)
app.include_router(customers.router)
app.include_router(cafes.router)
app.include_router(slots.router)
