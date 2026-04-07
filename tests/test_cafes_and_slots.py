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


def test_get_cafe_by_join_code(client):
    _, token = make_owner(client, "cafeowner2@test.com")
    cafe = make_cafe(client, token, name="Join Code Cafe")
    res = client.get(f"/cafes/join/{cafe['join_code']}")
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
