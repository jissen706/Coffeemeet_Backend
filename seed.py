"""
Seed script — run once to populate the DB with dummy data for testing.
Usage: python seed.py
"""
import sys
from datetime import date, datetime, timedelta
from database import SessionLocal, engine, Base
import models
from argon2 import PasswordHasher

ph = PasswordHasher()

# ── helpers ──────────────────────────────────────────────────────────────────

def dt(day_offset, hour, minute=0):
    """Return a datetime relative to today."""
    d = date.today() + timedelta(days=day_offset)
    return datetime(d.year, d.month, d.day, hour, minute)

# ── main ─────────────────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # ── Owner ──────────────────────────────────────────────────────────────
    owner_email = "alice@coffeemeet.dev"
    owner = db.query(models.Owner).filter_by(email=owner_email).first()
    if not owner:
        owner = models.Owner(
            name="Alice Brewer",
            email=owner_email,
            hashed_password=ph.hash("password123"),
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        print(f"Created owner: {owner.email}")
    else:
        print(f"Owner already exists: {owner.email}")

    # ── Cafe ───────────────────────────────────────────────────────────────
    cafe = db.query(models.Cafe).filter_by(owner_id=owner.id).first()
    if not cafe:
        cafe = models.Cafe(
            name="The Daily Grind",
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=12),
            owner_id=owner.id,
            one_slot=True,
            join_code="DEMO01",
        )
        db.add(cafe)
        db.commit()
        db.refresh(cafe)
        print(f"Created cafe: {cafe.name}  (join_code={cafe.join_code})")
    else:
        print(f"Cafe already exists: {cafe.name}")

    # ── Baristas ───────────────────────────────────────────────────────────
    barista_data = [
        ("Marco Rossi",   "marco@coffeemeet.dev",   "555-0101"),
        ("Yuki Tanaka",   "yuki@coffeemeet.dev",    "555-0102"),
        ("Sofia Perez",   "sofia@coffeemeet.dev",   None),
    ]
    baristas = []
    for name, email, phone in barista_data:
        b = db.query(models.Barista).filter_by(email=email).first()
        if not b:
            b = models.Barista(name=name, email=email, phone_number=phone, cafe_id=cafe.id)
            db.add(b)
            db.commit()
            db.refresh(b)
            print(f"Created barista: {b.name}")
        baristas.append(b)

    # ── Customers ──────────────────────────────────────────────────────────
    customer_data = [
        ("Ben Carter",    "ben@example.com"),
        ("Priya Singh",   "priya@example.com"),
        ("Lucas Weber",   "lucas@example.com"),
        ("Emma Johansson","emma@example.com"),
    ]
    customers = []
    for name, email in customer_data:
        c = db.query(models.Customer).filter_by(email=email).first()
        if not c:
            c = models.Customer(name=name, email=email, cafe_id=cafe.id)
            db.add(c)
            db.commit()
            db.refresh(c)
            print(f"Created customer: {c.name}")
        customers.append(c)

    # ── Slots ──────────────────────────────────────────────────────────────
    # Only create slots if none exist yet for this cafe
    existing_slots = db.query(models.Slot).filter_by(cafe_id=cafe.id).count()
    if existing_slots == 0:
        slots_def = [
            # (day_offset, start_h, end_h, barista_idx, customer_idx or None, location)
            # ── yesterday ──
            (-1,  9,  9, 0, 0,    "Table 3"),
            (-1, 10, 10, 1, 1,    "Counter"),
            (-1, 11, 11, 2, None, "Window Seat"),   # open
            # ── today ──
            ( 0,  9,  9, 0, 2,    "Table 3"),
            ( 0, 10, 10, 0, None, "Table 3"),       # open
            ( 0, 11, 11, 1, 3,    "Patio"),
            ( 0, 12, 12, 1, None, "Patio"),         # open
            ( 0, 14, 14, 2, None, "Window Seat"),   # open
            ( 0, 15, 15, 2, None, "Window Seat"),   # open
            # ── tomorrow ──
            ( 1,  9,  9, 0, None, "Table 3"),
            ( 1, 10, 10, 1, None, "Counter"),
            ( 1, 11, 11, 0, None, "Table 3"),
            ( 1, 13, 13, 2, None, "Patio"),
            # ── day +2 ──
            ( 2,  9,  9, 1, None, "Counter"),
            ( 2, 10, 10, 2, None, "Window Seat"),
            ( 2, 14, 14, 0, None, "Table 3"),
            # ── day +3 ──
            ( 3, 10, 10, 0, None, "Table 3"),
            ( 3, 11, 11, 1, None, "Counter"),
            ( 3, 15, 15, 2, None, "Patio"),
        ]
        for day_off, sh, eh, bi, ci, loc in slots_def:
            slot = models.Slot(
                start_time=dt(day_off, sh, 0),
                end_time=dt(day_off, eh, 30),
                location=loc,
                cafe_id=cafe.id,
                barista_id=baristas[bi].id,
                status="open" if ci is None else "booked",
            )
            db.add(slot)
            db.flush()
            if ci is not None:
                db.add(models.SlotBooking(slot_id=slot.id, customer_id=customers[ci].id))
        db.commit()
        print(f"Created {len(slots_def)} slots")
    else:
        print(f"Slots already exist ({existing_slots}), skipping")

    print("\n── Seed complete ──────────────────────────────────────────")
    print(f"  Login:      {owner_email}  /  password123")
    print(f"  Join code:  {cafe.join_code}")
    print(f"  Customer:   http://localhost:5173/cafe/{cafe.join_code}")
    print(f"  Barista:    http://localhost:5173/barista?code={cafe.join_code}")

finally:
    db.close()
