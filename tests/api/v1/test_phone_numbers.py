import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient

from secunda_assignment.main import app
from secunda_assignment.api.v1.phone_numbers import get_phone_number_repo
from secunda_assignment.storage.repositories import PhoneNumberRepository
from secunda_assignment.storage.exceptions import (
    PhoneNumberNotFound,
    OrganizationNotFound,
)
from secunda_assignment.storage import schemas


phone_number_str = "tel:+7-987-654-32-10"


@pytest.fixture
def mock_phone_number_repo() -> MagicMock:
    """Fixture to create a mock PhoneNumberRepository."""
    mock = MagicMock(spec=PhoneNumberRepository)
    mock.create = AsyncMock()
    mock.get_all = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_create_phone_number(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test creating a phone number successfully."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone_read = schemas.PhoneNumberRead(
        id=1, number=phone_number_str, phone_type="main", organization_id=1
    )
    mock_phone_number_repo.create.return_value = mock_phone_read

    phone_create_data = {
        "number": phone_number_str,
        "phone_type": "main",
        "organization_id": 1,
    }
    response = await test_client.post("/api/v1/phones/", json=phone_create_data)

    assert response.status_code == 201
    assert response.json() == mock_phone_read.model_dump()
    mock_phone_number_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_phone_number_org_not_found(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test creating a phone number for a non-existent organization."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone_number_repo.create.side_effect = OrganizationNotFound

    phone_create_data = {
        "number": phone_number_str,
        "phone_type": "main",
        "organization_id": 123,
    }
    response = await test_client.post("/api/v1/phones/", json=phone_create_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Organization not found"}


@pytest.mark.asyncio
async def test_get_all_phone_numbers(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test getting all phone numbers."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phones = [
        schemas.PhoneNumberRead(
            id=1, number=phone_number_str, phone_type="main", organization_id=1
        )
    ]
    mock_phone_number_repo.get_all.return_value = mock_phones

    response = await test_client.get("/api/v1/phones/")

    assert response.status_code == 200
    assert response.json() == [p.model_dump() for p in mock_phones]


@pytest.mark.asyncio
async def test_get_phone_number(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test getting a single phone number by ID."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone = schemas.PhoneNumberRead(
        id=1, number=phone_number_str, phone_type="main", organization_id=1
    )
    mock_phone_number_repo.get_by_id.return_value = mock_phone

    response = await test_client.get("/api/v1/phones/1")

    assert response.status_code == 200
    assert response.json() == mock_phone.model_dump()


@pytest.mark.asyncio
async def test_get_phone_number_not_found(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test getting a phone number that does not exist."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone_number_repo.get_by_id.return_value = None

    response = await test_client.get("/api/v1/phones/123")

    assert response.status_code == 404
    assert response.json() == {"detail": "Phone number not found"}


@pytest.mark.asyncio
async def test_update_phone_number(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test updating a phone number successfully."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    updated_phone = schemas.PhoneNumberRead(
        id=1, number=phone_number_str, phone_type="work", organization_id=1
    )
    mock_phone_number_repo.update.return_value = updated_phone

    update_data = {"number": phone_number_str, "phone_type": "work"}
    response = await test_client.put("/api/v1/phones/1", json=update_data)

    assert response.status_code == 200
    assert response.json() == updated_phone.model_dump()


@pytest.mark.asyncio
async def test_update_phone_number_not_found(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test updating a phone number that does not exist."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone_number_repo.update.side_effect = PhoneNumberNotFound

    update_data = {"number": phone_number_str, "phone_type": "asdf"}
    response = await test_client.put("/api/v1/phones/123", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_phone_number(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test deleting a phone number successfully."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone = schemas.PhoneNumberRead(
        id=1, number=phone_number_str, phone_type="main", organization_id=1
    )
    mock_phone_number_repo.get_by_id.return_value = mock_phone
    mock_phone_number_repo.delete.return_value = None

    response = await test_client.delete("/api/v1/phones/1")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_phone_number_not_found(
    test_client: AsyncClient, mock_phone_number_repo: MagicMock
):
    """Test deleting a phone number that does not exist."""

    app.dependency_overrides[get_phone_number_repo] = lambda: mock_phone_number_repo

    mock_phone_number_repo.get_by_id.return_value = None

    response = await test_client.delete("/api/v1/phones/123")

    assert response.status_code == 404
