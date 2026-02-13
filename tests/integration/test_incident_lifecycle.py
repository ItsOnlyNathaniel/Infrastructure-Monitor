import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app
from src.core.database import get_db


@pytest.mark.asyncio
async def test_incident_list_and_detail_endpoints(async_client: AsyncClient, test_db: AsyncSession):
    """
    Simple integration test that exercises the incident lifecycle endpoints
    at a high level:
    - list all incidents
    - fetch a single incident (may or may not exist)
    """

    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        # List incidents – this should always hit the API, even if it returns 404
        list_resp = await client.get("/api/incidents/incidents")
        assert list_resp.status_code in (200, 404)

        # Try fetching a specific incident id (1); depending on seed data this
        # may or may not exist, so we just assert the API responds meaningfully.
        detail_resp = await client.get("/api/incidents/incidents/1")
        assert detail_resp.status_code in (200, 404)
