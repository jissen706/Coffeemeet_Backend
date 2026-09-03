"""Integration tests for cafe creation, barista/customer flows, and slot booking."""

import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

def get_cafe_customers(client, cafe_id, token):
    return client.get(f"/cafes/{cafe_id}/customers", headers={"Authorization": f"Bearer {token}"})


def make_owner(client, email="owner@test.com"):
    res = client.post("/owners", json={"name": "Owner", "email": email, "password": "pw123"})
    assert res.status_code == 200
    d = res.json()
    return d["user"]["id"], d["access_token"]


def make_cafe(client, token, name="Test Cafe"):
    res = client.post(
        "/cafes",
        json={"name": name, "start_date": "2030-01-01", "end_date": "2030-01-31", "one_slot": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    return res.json()


def join_barista(client, join_code, email="barista@test.com"):
    res = client.post(
        "/baristas",
        json={"name": "Marco", "email": email, "join_code": join_code},
    )
    assert res.status_code == 200
    return res.json()


def join_customer(client, cafe_id, email="customer@test.com"):
    res = client.post(f"/customers/{cafe_id}", json={"name": "Ben", "email": email})
    assert res.status_code == 200
    return res.json()


# ── cafe tests ─────────────────────────────────────────────────────────────────

def test_create_cafe_requires_owner_token(client):
    res = client.post(
        "/cafes",
        json={"name": "X", "start_date": "2030-01-01", "end_date": "2030-01-31", "one_slot": True},
    )
    assert res.status_code in (401, 403)


def test_create_cafe_success(client):
    _, token = make_owner(client, "cafeowner@test.com")
    cafe = make_cafe(client, token)
    assert "join_code" in cafe
    assert len(cafe["join_code"]) == 6
    assert cafe["name"] == "Test Cafe"


def test_get_cafe_by_participant_code(client):
    _, token = make_owner(client, "cafeowner2@test.com")
    cafe = make_cafe(client, token, name="Join Code Cafe")
    res = client.get(f"/cafes/join/{cafe['participant_code']}")
    assert res.status_code == 200
    assert res.json()["id"] == cafe["id"]


def test_get_cafe_by_bad_code_returns_404(client):
    res = client.get("/cafes/join/XXXXXX")
    assert res.status_code == 404


# ── barista + customer tests ───────────────────────────────────────────────────

def test_barista_join_and_login_idempotent(client):
    _, token = make_owner(client, "bo3@test.com")
    cafe = make_cafe(client, token)
    first = join_barista(client, cafe["join_code"], "barista2@test.com")
    second = join_barista(client, cafe["join_code"], "barista2@test.com")
    # Same barista — should return a token both times
    assert "access_token" in first
    assert "access_token" in second
    assert first["user"]["id"] == second["user"]["id"]


def test_customer_register_twice_same_id(client):
    _, token = make_owner(client, "bo4@test.com")
    cafe = make_cafe(client, token)
    first = join_customer(client, cafe["id"], "cust2@test.com")
    second = join_customer(client, cafe["id"], "cust2@test.com")
    assert first["user"]["id"] == second["user"]["id"]


# ── slot booking tests ─────────────────────────────────────────────────────────

@pytest.fixture()
def booking_setup(client):
    """Returns (cafe, barista_token, barista_id, customer_id)."""
    _, owner_token = make_owner(client, "slotowner@test.com")
    cafe = make_cafe(client, owner_token)

    barista_data = join_barista(client, cafe["join_code"], "slotbarista@test.com")
    barista_token = barista_data["access_token"]
    barista_id = barista_data["user"]["id"]

    customer_data = join_customer(client, cafe["id"], "slotcustomer@test.com")
    customer_id = customer_data["user"]["id"]

    return cafe, barista_token, barista_id, customer_id


def test_create_slot_requires_barista_token(client, booking_setup):
    cafe, _, barista_id, _ = booking_setup
    res = client.post("/slots", json={
        "cafe_id": cafe["id"], "barista_id": barista_id,
        "start_time": "2030-01-10T09:00:00", "end_time": "2030-01-10T10:00:00",
        "location": "Table 1",
    })
    assert res.status_code in (401, 403)


def test_create_and_book_slot(client, booking_setup):
    cafe, barista_token, barista_id, customer_id = booking_setup

    slot_res = client.post(
        "/slots",
        json={
            "cafe_id": cafe["id"], "barista_id": barista_id,
            "start_time": "2030-01-10T09:00:00", "end_time": "2030-01-10T10:00:00",
            "location": "Table 2",
        },
        headers={"Authorization": f"Bearer {barista_token}"},
    )
    assert slot_res.status_code == 200
    slot = slot_res.json()
    assert slot["status"] == "open"

    book_res = client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_id})
    assert book_res.status_code == 200
    assert book_res.json()["status"] == "booked"


def test_one_slot_enforcement(client, booking_setup):
    cafe, barista_token, barista_id, customer_id = booking_setup

    def make_slot(start, end):
        res = client.post(
            "/slots",
            json={
                "cafe_id": cafe["id"], "barista_id": barista_id,
                "start_time": start, "end_time": end, "location": "Table 3",
            },
            headers={"Authorization": f"Bearer {barista_token}"},
        )
        assert res.status_code == 200
        return res.json()

    slot1 = make_slot("2030-01-15T09:00:00", "2030-01-15T10:00:00")
    slot2 = make_slot("2030-01-15T10:00:00", "2030-01-15T11:00:00")

    # Book first slot — should succeed
    client.put(f"/slots/{slot1['id']}/book", json={"customer_id": customer_id})

    # Book second slot — should fail (one_slot=True on this cafe)
    res = client.put(f"/slots/{slot2['id']}/book", json={"customer_id": customer_id})
    assert res.status_code == 400
    assert "already have a booking" in res.json()["detail"]


def test_book_already_booked_slot_fails(client, booking_setup):
    cafe, barista_token, barista_id, customer_id = booking_setup

    slot = client.post(
        "/slots",
        json={
            "cafe_id": cafe["id"], "barista_id": barista_id,
            "start_time": "2030-01-20T09:00:00", "end_time": "2030-01-20T10:00:00",
            "location": "Table 4",
        },
        headers={"Authorization": f"Bearer {barista_token}"},
    ).json()

    client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_id})
    res = client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_id})
    assert res.status_code == 400
    assert "already booked" in res.json()["detail"]


# ── new auth rule tests ────────────────────────────────────────────────────────

def test_get_customers_requires_owner_token(client):
    _, token = make_owner(client, "authtest@test.com")
    cafe = make_cafe(client, token)
    # No token
    res = client.get(f"/cafes/{cafe['id']}/customers")
    assert res.status_code in (401, 403)


def test_get_customers_wrong_owner_denied(client):
    _, token1 = make_owner(client, "owner1@test.com")
    _, token2 = make_owner(client, "owner2@test.com")
    cafe1 = make_cafe(client, token1)
    # owner2 tries to read owner1's customers
    res = get_cafe_customers(client, cafe1["id"], token2)
    assert res.status_code in (401, 403, 404)


def test_get_owner_cafes_requires_own_token(client):
    owner_id, token = make_owner(client, "cafelist@test.com")
    # Valid request — own token
    res = client.get(f"/owners/{owner_id}/cafes", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_get_owner_cafes_wrong_owner_denied(client):
    owner1_id, _ = make_owner(client, "cafelist1@test.com")
    _, token2 = make_owner(client, "cafelist2@test.com")
    # token2 tries to read owner1's cafe list
    res = client.get(f"/owners/{owner1_id}/cafes", headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 403


def test_cafe_reminder_minutes_round_trip(client):
    """Reminder offsets persist on create + update and come back deduped/sorted."""
    _, owner_token = make_owner(client, "remowner@test.com")
    res = client.post(
        "/cafes",
        json={
            "name": "Reminder Cafe",
            "start_date": "2030-04-01",
            "end_date": "2030-04-30",
            "one_slot": True,
            "reminder_minutes_before": [60, 5, 60, "1440"],  # dirty input
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 200, res.text
    cafe = res.json()
    assert cafe["reminder_minutes_before"] == [5, 60, 1440]

    # Update — clear it
    upd = client.put(
        f"/cafes/{cafe['id']}",
        json={"reminder_minutes_before": []},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert upd.status_code == 200
    assert upd.json()["reminder_minutes_before"] == []


def test_reminder_scheduler_sends_once_per_offset(monkeypatch):
    """Drives reminders._tick directly with fixed time to verify it sends once
    per (slot,customer,minutes) and never re-sends."""
    import models, reminders
    from database import SessionLocal
    from datetime import datetime, timedelta

    sent = []
    monkeypatch.setattr(
        reminders, "send_reminder_email",
        lambda **kw: sent.append((kw["customer_email"], kw["minutes_before"])),
    )

    db = SessionLocal()
    try:
        # Build minimal fixture: owner → cafe (with reminders) → barista, customer, slot+booking
        owner = models.Owner(name="O", email="rs_owner@x", hashed_password="x")
        db.add(owner); db.commit(); db.refresh(owner)

        slot_start = datetime.utcnow() + timedelta(minutes=4)  # in 4 minutes — falls into the "5 min before" window
        cafe = models.Cafe(
            name="RS", start_date=slot_start.date(), end_date=slot_start.date(),
            owner_id=owner.id, one_slot=True, reminder_minutes_before="5,60",
            join_code="RSCODE", participant_code="RSPART",
        )
        db.add(cafe); db.commit(); db.refresh(cafe)

        barista = models.Barista(name="B", email="rs_b@x", cafe_id=cafe.id)
        cust = models.Customer(name="C", email="rs_c@x", cafe_id=cafe.id)
        db.add_all([barista, cust]); db.commit()
        db.refresh(barista); db.refresh(cust)

        slot = models.Slot(
            start_time=slot_start, end_time=slot_start + timedelta(minutes=15),
            location="Counter", cafe_id=cafe.id, barista_id=barista.id, status="open",
        )
        db.add(slot); db.commit(); db.refresh(slot)
        db.add(models.SlotBooking(slot_id=slot.id, customer_id=cust.id))
        db.commit()
    finally:
        db.close()

    # First tick — should send the 5-minute reminder, NOT the 60-minute one.
    reminders._tick()
    assert ("rs_c@x", 5) in sent
    assert all(m != 60 for _, m in sent)

    # Second tick — should NOT re-send (dedup row exists).
    sent.clear()
    reminders._tick()
    assert sent == []


def test_manual_slot_creates_and_books(client):
    """Owner creates a manual slot AND books two participants in one call."""
    _, owner_token = make_owner(client, "manualowner@test.com")
    cafe_res = client.post(
        "/cafes",
        json={
            "name": "Manual Cafe",
            "start_date": "2030-03-01",
            "end_date": "2030-03-31",
            "one_slot": True,
            "max_participants": 2,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    cafe = cafe_res.json()

    barista = join_barista(client, cafe["join_code"], "manbar@test.com")
    c1 = join_customer(client, cafe["id"], "manc1@test.com")
    c2 = join_customer(client, cafe["id"], "manc2@test.com")

    res = client.post(
        "/slots/manual",
        json={
            "cafe_id": cafe["id"],
            "barista_id": barista["user"]["id"],
            "customer_ids": [c1["user"]["id"], c2["user"]["id"]],
            "start_time": "2030-03-15T10:00:00",
            "end_time": "2030-03-15T10:30:00",
            "location": "Big Table",
            "notes": "Rescheduled from earlier",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 200, res.text
    slot = res.json()
    assert slot["status"] == "booked"  # at capacity
    assert slot["spots_left"] == 0
    assert slot["max_participants"] == 2
    assert {c["id"] for c in slot["customers"]} == {c1["user"]["id"], c2["user"]["id"]}
    assert slot["notes"] == "Rescheduled from earlier"


def test_manual_slot_rejects_other_owners(client):
    _, owner_a = make_owner(client, "manown_a@test.com")
    _, owner_b = make_owner(client, "manown_b@test.com")
    cafe = make_cafe(client, owner_a, name="Manual Auth Cafe")
    barista = join_barista(client, cafe["join_code"], "manbar2@test.com")
    cust = join_customer(client, cafe["id"], "manc3@test.com")

    res = client.post(
        "/slots/manual",
        json={
            "cafe_id": cafe["id"],
            "barista_id": barista["user"]["id"],
            "customer_ids": [cust["user"]["id"]],
            "start_time": "2030-01-15T09:00:00",
            "end_time": "2030-01-15T09:30:00",
            "location": "Counter",
        },
        headers={"Authorization": f"Bearer {owner_b}"},
    )
    assert res.status_code in (403, 404)


def test_manual_slot_caps_at_max_participants(client):
    _, owner_token = make_owner(client, "mancap@test.com")
    cafe = make_cafe(client, owner_token, name="Cap Cafe")  # default max_participants=1
    barista = join_barista(client, cafe["join_code"], "mancapbar@test.com")
    c1 = join_customer(client, cafe["id"], "mancapc1@test.com")
    c2 = join_customer(client, cafe["id"], "mancapc2@test.com")

    res = client.post(
        "/slots/manual",
        json={
            "cafe_id": cafe["id"],
            "barista_id": barista["user"]["id"],
            "customer_ids": [c1["user"]["id"], c2["user"]["id"]],
            "start_time": "2030-01-20T10:00:00",
            "end_time": "2030-01-20T10:30:00",
            "location": "Counter",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400


def test_group_chat_capacity(client):
    """A cafe with max_participants=3 keeps slots open until the 3rd booking lands."""
    _, owner_token = make_owner(client, "groupowner@test.com")
    res = client.post(
        "/cafes",
        json={
            "name": "Group Cafe",
            "start_date": "2030-02-01",
            "end_date": "2030-02-28",
            "one_slot": False,
            "max_participants": 3,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 200
    cafe = res.json()
    assert cafe["max_participants"] == 3

    barista = join_barista(client, cafe["join_code"], "groupbar@test.com")
    barista_token = barista["access_token"]
    barista_id = barista["user"]["id"]

    slot = client.post(
        "/slots",
        json={
            "cafe_id": cafe["id"], "barista_id": barista_id,
            "start_time": "2030-02-10T09:00:00", "end_time": "2030-02-10T10:00:00",
            "location": "Big Table",
        },
        headers={"Authorization": f"Bearer {barista_token}"},
    ).json()

    customer_ids = []
    for i in range(3):
        c = join_customer(client, cafe["id"], f"groupc{i}@test.com")
        customer_ids.append(c["user"]["id"])

    # First two bookings keep the slot open with shrinking spots_left.
    r1 = client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_ids[0]})
    assert r1.status_code == 200
    assert r1.json()["status"] == "open"
    assert r1.json()["spots_left"] == 2

    r2 = client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_ids[1]})
    assert r2.json()["status"] == "open"
    assert r2.json()["spots_left"] == 1

    # Third fills it — flips to booked.
    r3 = client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer_ids[2]})
    assert r3.json()["status"] == "booked"
    assert r3.json()["spots_left"] == 0
    assert len(r3.json()["customers"]) == 3

    # Fourth attempt is rejected.
    extra = join_customer(client, cafe["id"], "groupc_extra@test.com")
    r4 = client.put(f"/slots/{slot['id']}/book", json={"customer_id": extra["user"]["id"]})
    assert r4.status_code == 400


def test_barista_cannot_create_slot_for_other_barista(client):
    _, token = make_owner(client, "slotauth@test.com")
    cafe = make_cafe(client, token)
    b1 = join_barista(client, cafe["join_code"], "b1@test.com")
    b2 = join_barista(client, cafe["join_code"], "b2@test.com")
    # b1 tries to create a slot attributed to b2
    res = client.post(
        "/slots",
        json={
            "cafe_id": cafe["id"], "barista_id": b2["user"]["id"],
            "start_time": "2030-01-05T09:00:00", "end_time": "2030-01-05T10:00:00",
            "location": "Table X",
        },
        headers={"Authorization": f"Bearer {b1['access_token']}"},
    )
    assert res.status_code == 403


def test_barista_cannot_update_other_baristas_meet_link(client):
    _, token = make_owner(client, "meetlink@test.com")
    cafe = make_cafe(client, token)
    b1 = join_barista(client, cafe["join_code"], "ml1@test.com")
    b2 = join_barista(client, cafe["join_code"], "ml2@test.com")
    customer = join_customer(client, cafe["id"], "mlcust@test.com")

    # b1 creates and books a slot
    slot = client.post(
        "/slots",
        json={
            "cafe_id": cafe["id"], "barista_id": b1["user"]["id"],
            "start_time": "2030-01-06T09:00:00", "end_time": "2030-01-06T10:00:00",
            "location": "Table Y",
        },
        headers={"Authorization": f"Bearer {b1['access_token']}"},
    ).json()
    client.put(f"/slots/{slot['id']}/book", json={"customer_id": customer["user"]["id"]})

    # b2 tries to set meet link on b1's slot
    res = client.patch(
        f"/slots/{slot['id']}/meet-link",
        json={"meet_link": "https://meet.google.com/fake"},
        headers={"Authorization": f"Bearer {b2['access_token']}"},
    )
    assert res.status_code == 403
