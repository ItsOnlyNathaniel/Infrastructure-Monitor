# conftest.py - Unit test configuration and fixtures for FastAPI application
# pylint: disable=redefined-outer-name
#Imports
from typing import Generator
import pytest  # type: ignore
import httpx  # type: ignore
import os
from fastapi.testclient import TestClient  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy.pool import StaticPool  # type: ignore

from src.api.main import app
from src.database.models import Base
from src.core.database import get_db
from src.services.MonitorService import MonitorService


# Setting up an in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Use a different session for testing
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Database setup/teardown fixture
@pytest.fixture(scope="function")
def db_session():
    """Create database tables and session for each test."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)


# Fixture for TestClient (for basic HTTP request testing)
@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client for making HTTP requests to the FastAPI app."""
    _ = db_session  # ensure fixture is requested to satisfy linters
    with TestClient(app) as test_client:
        yield test_client


# --- Dependency overrides used across tests ---
@pytest.fixture()
def override_monitor_check(monkeypatch):
    async def fake_check_resources(_self, resource_type: str, resource_ids):
        return [
            {
                "resource_id": resource_ids[0],
                "resource_type": resource_type,
                "status": "healthy",
                "last_check": "2024-01-01T00:00:00Z",
                "issues": [],
            }
        ]

    monkeypatch.setattr(MonitorService, "check_resources", fake_check_resources)
    return fake_check_resources


@pytest.fixture()
def override_monitor_get(monkeypatch):
    async def fake_get_resource_status(_self, rt: str, rid: str):
        return {
            "resource_id": rid,
            "resource_type": rt,
            "status": "healthy",
            "last_check": "2024-01-01T00:00:00Z",
            "issues": [],
        }

    monkeypatch.setattr(MonitorService, "get_resource_status", fake_get_resource_status)
    return fake_get_resource_status


@pytest.fixture()
def override_db():
    async def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db
    yield _override_get_db
    app.dependency_overrides.clear()


# Fixture for testing against Docker container
@pytest.fixture(scope="session")
def docker_client():
    """Create an HTTP client for testing against the Dockerized server."""
    docker_url = os.getenv("DOCKER_TEST_URL", "http://localhost:8000")
    
    # Check if Docker container is running
    with httpx.Client(base_url=docker_url, timeout=10.0) as client:
        try:
            # Test connection
            response = client.get("/")
            if response.status_code == 200:
                yield client
            else:
                pytest.skip("Docker container not responding correctly at %s", docker_url)
        except httpx.ConnectError:
            pytest.skip("Docker container not accessible at %s. Make sure it's running.", docker_url)
       