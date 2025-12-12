#Imports
from typing import Generator
import pytest
import httpx
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.database.models import Base


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
    with TestClient(app) as test_client:
        yield test_client


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
                pytest.skip(f"Docker container not responding correctly at {docker_url}")
        except httpx.ConnectError:
            pytest.skip(f"Docker container not accessible at {docker_url}. Make sure it's running.")
       