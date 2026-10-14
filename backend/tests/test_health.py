import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "beacon-console"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "beacon-console"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_db_endpoint(client: AsyncClient):
    response = await client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert data["database"] in ("connected", "error")


@pytest.mark.asyncio
async def test_docs_available_in_dev(client: AsyncClient):
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")