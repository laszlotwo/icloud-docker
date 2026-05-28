import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DATA_DIR", "/tmp/home-ai-test")

from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def db_engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    LocalSession = sessionmaker(bind=db_engine)
    session = LocalSession()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Skip Alembic and scheduler during tests
    with patch("app.main.init_db"), patch("app.main.get_scheduler") as mock_scheduler, \
         patch("app.main.restore_reminder_jobs"):
        mock_scheduler.return_value.start = lambda: None
        mock_scheduler.return_value.shutdown = lambda: None
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()
