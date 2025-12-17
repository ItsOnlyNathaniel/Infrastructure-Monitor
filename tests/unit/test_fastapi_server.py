"""
This module includes:
- Tests for basic HTTP requests using TestClient (client fixture)
- Tests for server running through Docker (docker_client fixture)
"""


def test_root_endpoint_basic_http(client):
    """Test basic HTTP request to root endpoint using TestClient."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Infrastructure Monitor"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_root_endpoint_docker(docker_client):
    """Test root endpoint against Docker container."""
    response = docker_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Infrastructure Monitor"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_health_endpoint_basic_http(client):
    """Test health endpoint using TestClient."""
    response = client.get("/health/test-service")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service_id"] == "test-service"


def test_health_endpoint_docker(docker_client):
    """Test health endpoint against Docker container."""
    response = docker_client.get("/health/test-service")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service_id"] == "test-service"
