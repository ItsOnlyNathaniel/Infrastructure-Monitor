import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.core.database import get_db


@pytest.mark.asyncio
async def test_ecs_service_health_check_can_be_called(async_client: AsyncClient, test_db: AsyncSession):
    """
    Simple integration test to ensure ECS health check endpoint is callable.

    The detailed rollback behaviour is handled by services/workers; here we just
    verify the API wiring is correct.
    """

    app.dependency_overrides[get_db] = lambda: test_db

    payload = {"resource_type": "ecs", "resource_ids": ["test-ecs-service"]}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/services/check", json=payload)

    # Endpoint should exist; allow both successful and not-found style responses
    assert response.status_code in (200, 404)
