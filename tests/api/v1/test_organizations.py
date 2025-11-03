import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient

from secunda_assignment.main import app
from secunda_assignment.api.v1.organizations import get_organization_repo
from secunda_assignment.storage.repositories import OrganizationRepository
from secunda_assignment.storage.exceptions import (
    OrganizationNotFound,
    BuildingNotFound,
)
from secunda_assignment.storage import schemas


@pytest.fixture
def mock_organization_repo() -> MagicMock:
    """Fixture to create a mock OrganizationRepository."""
    mock = MagicMock(spec=OrganizationRepository)
    mock.create = AsyncMock()
    mock.get_all = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.get_by_name = AsyncMock()
    mock.get_by_building_id = AsyncMock()
    mock.get_by_category_path = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.find_in_radius = AsyncMock()
    mock.find_in_bbox = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_create_organization(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test creating an organization successfully."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_org_read = schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)
    mock_organization_repo.create.return_value = mock_org_read

    org_create_data = {"name": "Test Corp", "building_id": 1}
    response = await test_client.post("/api/v1/organizations/", json=org_create_data)

    assert response.status_code == 201
    assert response.json() == mock_org_read.model_dump()
    mock_organization_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_organization_building_not_found(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test creating an organization with a non-existent building."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_organization_repo.create.side_effect = BuildingNotFound

    org_create_data = {"name": "Test Corp", "building_id": 123}
    response = await test_client.post("/api/v1/organizations/", json=org_create_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Building not found"}


@pytest.mark.asyncio
async def test_get_all_organizations(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting all organizations."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_orgs = [schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)]
    mock_organization_repo.get_all.return_value = mock_orgs

    response = await test_client.get("/api/v1/organizations/")

    assert response.status_code == 200
    assert response.json() == [org.model_dump() for org in mock_orgs]


@pytest.mark.asyncio
async def test_get_organization_by_name(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting an organization by name."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_org = schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)
    mock_organization_repo.get_by_name.return_value = mock_org

    response = await test_client.get("/api/v1/organizations/by-name?name=Test%20Corp")

    assert response.status_code == 200
    assert response.json() == mock_org.model_dump()


@pytest.mark.asyncio
async def test_get_organization_by_name_not_found(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting a non-existent organization by name."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_organization_repo.get_by_name.return_value = None

    response = await test_client.get("/api/v1/organizations/by-name?name=non-existent")

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}


@pytest.mark.asyncio
async def test_get_organizations_by_building(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting organizations by building ID."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_orgs = [schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)]
    mock_organization_repo.get_by_building_id.return_value = mock_orgs

    response = await test_client.get("/api/v1/organizations/by-building/1")

    assert response.status_code == 200
    assert response.json() == [org.model_dump() for org in mock_orgs]


@pytest.mark.asyncio
async def test_get_organizations_by_category(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting organizations by category path."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_orgs = [schemas.OrganizationRead(id=1, name="Pizza Place", building_id=1)]
    mock_organization_repo.get_by_category_path.return_value = mock_orgs

    response = await test_client.get(
        "/api/v1/organizations/by-category?path=food.pizza"
    )

    assert response.status_code == 200
    assert response.json() == [org.model_dump() for org in mock_orgs]


@pytest.mark.asyncio
async def test_get_organization(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting a single organization by ID."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_org = schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)
    mock_organization_repo.get_by_id.return_value = mock_org

    response = await test_client.get("/api/v1/organizations/1")

    assert response.status_code == 200
    assert response.json() == mock_org.model_dump()


@pytest.mark.asyncio
async def test_get_organization_not_found(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test getting a non-existent organization by ID."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_organization_repo.get_by_id.return_value = None

    response = await test_client.get("/api/v1/organizations/123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}


@pytest.mark.asyncio
async def test_update_organization(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test updating an organization successfully."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    updated_org = schemas.OrganizationRead(id=1, name="Updated Corp", building_id=1)
    mock_organization_repo.update.return_value = updated_org

    update_data = {"name": "Updated Corp"}
    response = await test_client.put("/api/v1/organizations/1", json=update_data)

    assert response.status_code == 200
    assert response.json() == updated_org.model_dump()
    mock_organization_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_organization_not_found(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test updating a non-existent organization."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_organization_repo.update.side_effect = OrganizationNotFound

    update_data = {"name": "New Name"}
    response = await test_client.put("/api/v1/organizations/123", json=update_data)

    assert response.status_code == 404
    assert response.json() == {"detail": ""}


@pytest.mark.asyncio
async def test_delete_organization(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test deleting an organization successfully."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_org = schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)
    mock_organization_repo.get_by_id.return_value = mock_org
    mock_organization_repo.delete.return_value = None

    response = await test_client.delete("/api/v1/organizations/1")

    assert response.status_code == 204
    mock_organization_repo.delete.assert_awaited_once_with(mock_org)


@pytest.mark.asyncio
async def test_delete_organization_not_found(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test deleting a non-existent organization."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_organization_repo.get_by_id.return_value = None

    response = await test_client.delete("/api/v1/organizations/123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}


@pytest.mark.asyncio
async def test_find_organizations_in_radius(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test finding organizations within a radius."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_orgs = [schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)]
    mock_organization_repo.find_in_radius.return_value = mock_orgs

    query_data = {
        "center": {"latitude": 55.7558, "longitude": 37.6173},
        "radius_meters": 1000,
    }
    response = await test_client.post(
        "/api/v1/organizations/find/radius", json=query_data
    )

    assert response.status_code == 200
    assert response.json() == [org.model_dump() for org in mock_orgs]


@pytest.mark.asyncio
async def test_find_organizations_in_bounding_box(
    test_client: AsyncClient, mock_organization_repo: MagicMock
):
    """Test finding organizations within a bounding box."""

    app.dependency_overrides[get_organization_repo] = lambda: mock_organization_repo

    mock_orgs = [schemas.OrganizationRead(id=1, name="Test Corp", building_id=1)]
    mock_organization_repo.find_in_bbox.return_value = mock_orgs

    query_data = {
        "top_left": {"latitude": 53.33, "longitude": 32.1},
        "bottom_right": {"latitude": 55.75, "longitude": 37.62},
    }
    response = await test_client.post(
        "/api/v1/organizations/find/bbox", json=query_data
    )

    assert response.status_code == 200
    assert response.json() == [org.model_dump() for org in mock_orgs]
