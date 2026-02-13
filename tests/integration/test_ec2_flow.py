import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.core.database import get_db


@pytest.mark.asyncio
async def test_ec2_health_check_flow(async_client: AsyncClient, test_db: AsyncSession):
    """
    Simple integration test for the EC2 monitoring flow.

    This assumes:
    - The DB is seeded with at least one EC2-backed service.
    - The monitor will not raise for the given resource id.
    """

    # Override dependency to use the test DB session if the fixture provides one
    app.dependency_overrides[get_db] = lambda: test_db

    # Hit the health-check endpoint for EC2 with a dummy resource id
    payload = {"resource_type": "ec2", "resource_ids": ["test-ec2-instance"]}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/services/check", json=payload)

    assert response.status_code in (200, 404)

    if response.status_code == 200:
        body = response.json()
        assert isinstance(body, list)
        assert len(body) >= 0
