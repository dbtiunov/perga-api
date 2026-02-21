import json
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set required environment variables for testing before importing app
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["CORS_ORIGINS"] = json.dumps(["http://localhost:5173", "http://localhost:3000"])

from app.core.database import Base, get_db
from app.main import app
from app.services.auth_utils import create_access_token


# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

pytest_plugins = [
    "app.tests.fixtures.auth",
]


@pytest.fixture(scope="function")
def test_engine():
    # Create the SQLite engine with check_same_thread=False to allow multiple threads
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_factory(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)  # noqa: N806
    return TestingSessionLocal


@pytest.fixture(scope="function")
def test_db(test_db_factory):
    db = test_db_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
