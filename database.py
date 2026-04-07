import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cafe.db")
# Railway sometimes issues postgres:// (old form); SQLAlchemy 2.x requires postgresql://
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL == "sqlite:///:memory:":
        # StaticPool pins all connections to a single in-memory DB,
        # which is required for testing (each new connection is otherwise empty).
        from sqlalchemy.pool import StaticPool
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args=_connect_args,
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()