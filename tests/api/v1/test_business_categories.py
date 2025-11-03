import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient

from secunda_assignment.main import app
from secunda_assignment.api.v1.business_categories import get_business_category_repo
from secunda_assignment.storage.repositories import BusinessCategoryRepository
from secunda_assignment.storage.exceptions import (
    BusinessCategoryNotFound,
    BusinessCategoryAlreadyExists,
)
from secunda_assignment.storage import schemas


@pytest.fixture
def mock_business_category_repo() -> MagicMock:
    """Fixture to create a mock BusinessCategoryRepository."""
    mock = MagicMock(spec=BusinessCategoryRepository)
    mock.create = AsyncMock()
    mock.get_all = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_create_business_category(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test creating a business category successfully."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_category_read = schemas.BusinessCategoryRead(id=1, name="Food", path="food")
    mock_business_category_repo.create.return_value = mock_category_read

    category_create_data = {"name": "Food", "path": "food"}
    response = await test_client.post(
        "/api/v1/business_categories/", json=category_create_data
    )

    assert response.status_code == 201
    assert response.json() == mock_category_read.model_dump()
    mock_business_category_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_business_category_conflict(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test creating a business category that already exists."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_business_category_repo.create.side_effect = BusinessCategoryAlreadyExists

    category_create_data = {"name": "Food", "path": "food"}
    response = await test_client.post(
        "/api/v1/business_categories/", json=category_create_data
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Business category path already exists"}


@pytest.mark.asyncio
async def test_get_all_business_categories(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test getting all business categories."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_categories = [schemas.BusinessCategoryRead(id=1, name="Food", path="food")]
    mock_business_category_repo.get_all.return_value = mock_categories

    response = await test_client.get("/api/v1/business_categories/")

    assert response.status_code == 200
    assert response.json() == [cat.model_dump() for cat in mock_categories]


@pytest.mark.asyncio
async def test_get_business_category(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test getting a single business category by ID."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_category = schemas.BusinessCategoryRead(id=1, name="Food", path="food")
    mock_business_category_repo.get_by_id.return_value = mock_category

    response = await test_client.get("/api/v1/business_categories/1")

    assert response.status_code == 200
    assert response.json() == mock_category.model_dump()


@pytest.mark.asyncio
async def test_get_business_category_not_found(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test getting a business category that does not exist."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_business_category_repo.get_by_id.return_value = None

    response = await test_client.get("/api/v1/business_categories/123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Business category not found"}


@pytest.mark.asyncio
async def test_update_business_category(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test updating a business category successfully."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    updated_category = schemas.BusinessCategoryRead(
        id=1, name="Updated Food", path="food"
    )
    mock_business_category_repo.update.return_value = updated_category

    update_data = {"name": "Updated Food"}
    response = await test_client.put("/api/v1/business_categories/1", json=update_data)

    assert response.status_code == 200
    assert response.json() == updated_category.model_dump()
    mock_business_category_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_business_category_not_found(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test updating a business category that does not exist."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_business_category_repo.update.side_effect = BusinessCategoryNotFound

    update_data = {"name": "New Name"}
    response = await test_client.put(
        "/api/v1/business_categories/123", json=update_data
    )

    assert response.status_code == 404
    assert response.json() == {"detail": ""}


@pytest.mark.asyncio
async def test_update_business_category_conflict(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test updating a business category that results in a conflict."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_business_category_repo.update.side_effect = BusinessCategoryAlreadyExists

    update_data = {"path": "existing-path"}
    response = await test_client.put("/api/v1/business_categories/1", json=update_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "Business category path already exists"}


@pytest.mark.asyncio
async def test_delete_business_category(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test deleting a business category successfully."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_category = schemas.BusinessCategoryRead(id=1, name="Food", path="food")
    mock_business_category_repo.get_by_id.return_value = mock_category
    mock_business_category_repo.delete.return_value = None

    response = await test_client.delete("/api/v1/business_categories/1")

    assert response.status_code == 204
    mock_business_category_repo.delete.assert_awaited_once_with(mock_category)


@pytest.mark.asyncio
async def test_delete_business_category_not_found(
    test_client: AsyncClient, mock_business_category_repo: MagicMock
):
    """Test deleting a business category that does not exist."""

    app.dependency_overrides[
        get_business_category_repo
    ] = lambda: mock_business_category_repo

    mock_business_category_repo.get_by_id.return_value = None

    response = await test_client.delete("/api/v1/business_categories/123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Business category not found"}
