"""Tests for JWT token creation, decoding, and role guards."""

import os
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException

import auth


SECRET = os.environ["SECRET_KEY"]


def test_create_token_contains_expected_claims():
    token = auth.create_token({"sub": "42", "role": "owner", "name": "Alice"})
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert payload["sub"] == "42"
    assert payload["role"] == "owner"
    assert payload["name"] == "Alice"
    assert "exp" in payload


def test_token_expiry_is_roughly_24h():
    token = auth.create_token({"sub": "1", "role": "owner"})
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = exp - now
    assert timedelta(hours=23) < delta < timedelta(hours=25)


def test_decode_token_valid():
    token = auth.create_token({"sub": "7", "role": "barista"})
    payload = auth.decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "barista"


def test_decode_token_invalid_raises_401():
    with pytest.raises(HTTPException) as exc:
        auth.decode_token("this.is.not.a.valid.token")
    assert exc.value.status_code == 401


def test_decode_token_wrong_secret_raises_401():
    bad_token = jwt.encode({"sub": "1", "role": "owner"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        auth.decode_token(bad_token)
    assert exc.value.status_code == 401


def test_secret_key_loaded_from_env():
    """SECRET_KEY must not be the old hardcoded placeholder."""
    assert auth.SECRET_KEY != "some-secret-string-change-this-later"
    assert len(auth.SECRET_KEY) >= 16
