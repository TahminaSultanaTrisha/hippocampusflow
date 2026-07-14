"""Test fixtures. Tests run on a throwaway in-memory SQLite database.

Two overrides make this work:
1. The get_db dependency -> requests use the test database.
2. analysis.SessionLocal -> background tasks (which open their own
   sessions) also use the test database instead of the real one.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.session import Base
from app.main import app
from app.services.ai import analysis

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client(monkeypatch):
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(analysis, "SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
