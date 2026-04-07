"""
Shared pytest fixtures.

We set env vars BEFORE importing any app modules, then reuse the same
engine that database.py creates so that create_all() and the test sessions
all share one in-memory SQLite instance.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Must happen before any app import that reads env vars at module level.
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:5173"

# Now import app modules — they will read the env vars we just set.
from database import engine, Base, get_db  # noqa: E402
from main import app                        # noqa: E402

_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    """Create all tables before each test and drop them after — guarantees isolation."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
