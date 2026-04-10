import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import engine, Base
import models
from routers import owners, baristas, customers, slots, cafes

load_dotenv()

Base.metadata.create_all(bind=engine)

# Idempotent migrations
from sqlalchemy import text
with engine.connect() as _conn:
    _conn.execute(text("ALTER TABLE baristas ADD COLUMN IF NOT EXISTS bio TEXT"))
    _conn.execute(text("ALTER TABLE cafes ADD COLUMN IF NOT EXISTS participant_code VARCHAR"))
    _conn.execute(text("ALTER TABLE slots ADD COLUMN IF NOT EXISTS notes TEXT"))
    # Backfill existing cafes that have no participant_code yet
    _conn.execute(text("""
        UPDATE cafes
        SET participant_code = UPPER(SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 6))
        WHERE participant_code IS NULL
    """))
    # Ensure uniqueness after backfill (retry any collisions)
    _conn.execute(text("""
        UPDATE cafes c
        SET participant_code = UPPER(SUBSTRING(MD5(c.id::TEXT || 'p') FROM 1 FOR 6))
        WHERE participant_code IN (
            SELECT participant_code FROM cafes GROUP BY participant_code HAVING COUNT(*) > 1
        )
    """))
    _conn.commit()

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
