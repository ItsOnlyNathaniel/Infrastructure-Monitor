"""
This module includes:
- Tests for basic HTTP requests using TestClient (client fixture)
- Tests for server running through Docker (docker_client fixture)
"""
import pytest  # type: ignore

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


def test_services_check_basic_http(client, override_monitor_check, override_db):
    """
    Exercise POST /api/services/check with the expected payload/shape.
    Uses monkeypatch to stub MonitorService so no external calls are made.
    """

    _ = override_monitor_check
    _ = override_db

    response = client.post(
        "/api/services/check",
        json={"resource_type": "ec2", "resource_ids": ["i-1234567890"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["resource_id"] == "i-1234567890"
    assert data[0]["resource_type"] == "ec2"
    assert data[0]["status"] == "healthy"
    assert data[0]["issues"] == []


@pytest.mark.parametrize(
    "resource_type,resource_id",
    [
        ("ec2", "i-abc123"),
        ("ecs", "task-xyz"),
    ],
)
def test_services_get_resource_status_basic_http(
    client, override_monitor_get, override_db, resource_type, resource_id
):
    """
    Exercise GET /api/services/{resource_type}/{resource_id} to validate the
    currently-designed contract while the endpoint is being built.
    """

    _ = override_monitor_get
    _ = override_db

    response = client.get(f"/api/services/{resource_type}/{resource_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["resource_id"] == resource_id
    assert payload["resource_type"] == resource_type
    assert payload["status"] == "healthy"
    assert isinstance(payload["issues"], list)


def test_services_check_docker(docker_client):
    """
    Basic contract check against Dockerized service. Uses real request shape so
    it exercises the currently-defined endpoint.
    """
    response = docker_client.post(
        "/api/services/check",
        json={"resource_type": "ec2", "resource_ids": ["i-1234567890"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "resource_id" in data[0]
    assert "status" in data[0]
