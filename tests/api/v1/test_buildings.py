import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient

from secunda_assignment.main import app
from secunda_assignment.api.v1.buildings import get_building_repo
from secunda_assignment.storage.repositories import BuildingRepository
from secunda_assignment.storage.exceptions import BuildingNotFound, AddressAlreadyExists
from secunda_assignment.storage import schemas


building_location = {"longitude": 10.0, "latitude": 20.0}


@pytest.fixture
def mock_building_repo() -> MagicMock:
    """Fixture to create a mock BuildingRepository."""
    mock = MagicMock(spec=BuildingRepository)
    mock.create = AsyncMock()
    mock.get_all = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.find_in_radius = AsyncMock()
    mock.find_in_bbox = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_create_building(test_client: AsyncClient, mock_building_repo: MagicMock):
    """Test creating a building successfully."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building_read = schemas.BuildingRead(
        id=1,
        address="123 Test St",
        location=building_location,
    )
    mock_building_repo.create.return_value = mock_building_read

    building_create_data = {
        "address": "123 Test St",
        "location": {"longitude": 10.0, "latitude": 20.0},
    }
    response = await test_client.post("/api/v1/buildings/", json=building_create_data)

    assert response.status_code == 201
    assert response.json() == mock_building_read.model_dump()
    mock_building_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_building_conflict(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test creating a building that already exists."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building_repo.create.side_effect = AddressAlreadyExists

    building_create_data = {
        "address": "123 Test St",
        "location": {"longitude": 10.0, "latitude": 20.0},
    }
    response = await test_client.post("/api/v1/buildings/", json=building_create_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "Building address already exists"}


@pytest.mark.asyncio
async def test_get_all_buildings(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test getting all buildings."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_buildings = [
        schemas.BuildingRead(
            id=1,
            address="123 Test St",
            location=building_location,
        )
    ]
    mock_building_repo.get_all.return_value = mock_buildings

    response = await test_client.get("/api/v1/buildings/")

    assert response.status_code == 200
    assert response.json() == [b.model_dump() for b in mock_buildings]


@pytest.mark.asyncio
async def test_get_building(test_client: AsyncClient, mock_building_repo: MagicMock):
    """Test getting a single building by ID."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building = schemas.BuildingRead(
        id=1,
        address="123 Test St",
        location=building_location,
    )
    mock_building_repo.get_by_id.return_value = mock_building

    response = await test_client.get("/api/v1/buildings/1")

    assert response.status_code == 200
    assert response.json() == mock_building.model_dump()


@pytest.mark.asyncio
async def test_get_building_not_found(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test getting a building that does not exist."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building_repo.get_by_id.return_value = None

    response = await test_client.get("/api/v1/buildings/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Building not found"}


@pytest.mark.asyncio
async def test_update_building(test_client: AsyncClient, mock_building_repo: MagicMock):
    """Test updating a building successfully."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    updated_building = schemas.BuildingRead(
        id=1,
        address="456 Updated St",
        location=building_location,
    )
    mock_building_repo.update.return_value = updated_building

    update_data = {"address": "456 Updated St"}
    response = await test_client.put("/api/v1/buildings/1", json=update_data)

    assert response.status_code == 200
    assert response.json() == updated_building.model_dump()


@pytest.mark.asyncio
async def test_update_building_not_found(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test updating a building that does not exist."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building_repo.update.side_effect = BuildingNotFound

    update_data = {"address": "456 Updated St"}
    response = await test_client.put("/api/v1/buildings/999", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_building(test_client: AsyncClient, mock_building_repo: MagicMock):
    """Test deleting a building successfully."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building = schemas.BuildingRead(
        id=1,
        address="123 Test St",
        location=building_location,
    )
    mock_building_repo.get_by_id.return_value = mock_building
    mock_building_repo.delete.return_value = None

    response = await test_client.delete("/api/v1/buildings/1")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_building_not_found(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test deleting a building that does not exist."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_building_repo.get_by_id.return_value = None

    response = await test_client.delete("/api/v1/buildings/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_find_buildings_in_radius(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test finding buildings within a radius."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_buildings = [
        schemas.BuildingRead(
            id=1,
            address="123 Test St",
            location=building_location,
        )
    ]
    mock_building_repo.find_in_radius.return_value = mock_buildings

    query_data = {
        "center": {"latitude": 20.0, "longitude": 10.0},
        "radius_meters": 1000,
    }
    response = await test_client.post("/api/v1/buildings/find/radius", json=query_data)

    assert response.status_code == 200
    assert response.json() == [b.model_dump() for b in mock_buildings]


@pytest.mark.asyncio
async def test_find_buildings_in_bounding_box(
    test_client: AsyncClient, mock_building_repo: MagicMock
):
    """Test finding buildings within a bounding box."""
    app.dependency_overrides[get_building_repo] = lambda: mock_building_repo
    mock_buildings = [
        schemas.BuildingRead(
            id=1,
            address="123 Test St",
            location=building_location,
        )
    ]
    mock_building_repo.find_in_bbox.return_value = mock_buildings

    query_data = {
        "top_left": {"latitude": 20.1, "longitude": 9.9},
        "bottom_right": {"latitude": 19.9, "longitude": 10.1},
    }
    response = await test_client.post("/api/v1/buildings/find/bbox", json=query_data)

    assert response.status_code == 200
    assert response.json() == [b.model_dump() for b in mock_buildings]
