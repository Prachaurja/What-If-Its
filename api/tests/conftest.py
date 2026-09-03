"""Tests run against a throwaway SQLite database so no Postgres is needed in CI."""
import os, pathlib
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
pathlib.Path("test.db").unlink(missing_ok=True)

import pytest
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app import models  # noqa: F401

@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

@pytest.fixture
def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
