"""Integration tests for owner registration, login, and cafe listing."""

import pytest


OWNER = {"name": "Alice", "email": "alice@example.com", "password": "hunter2"}


@pytest.fixture()
def registered_owner(client):
    res = client.post("/owners", json=OWNER)
    assert res.status_code == 200
    return res.json()


def test_register_owner_returns_token(client):
    res = client.post("/owners", json={"name": "Bob", "email": "bob@example.com", "password": "pass123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Bob"
    assert data["user"]["role"] == "owner"


def test_register_duplicate_email_fails(client, registered_owner):
    res = client.post("/owners", json=OWNER)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


def test_login_owner_success(client, registered_owner):
    res = client.post("/owners/login", json={"email": OWNER["email"], "password": OWNER["password"]})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_owner_wrong_password(client, registered_owner):
    res = client.post("/owners/login", json={"email": OWNER["email"], "password": "wrongpass"})
    assert res.status_code == 401


def test_login_owner_not_found(client):
    res = client.post("/owners/login", json={"email": "nobody@example.com", "password": "x"})
    assert res.status_code == 404


def test_get_owner_cafes_empty(client, registered_owner):
    owner_id = registered_owner["user"]["id"]
    token = registered_owner["access_token"]
    res = client.get(f"/owners/{owner_id}/cafes", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == []
