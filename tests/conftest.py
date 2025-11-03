import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from secunda_assignment.main import app
from secunda_assignment.security import get_api_key


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio", {"use_uvloop": True}


def get_api_key_override():
    return "test_api_key"


@pytest_asyncio.fixture(scope="function")
async def test_client() -> AsyncGenerator:
    """
    A fixture that provides an asynchronous test client for making requests to the application,
    with the API key dependency overridden for testing purposes.
    """

    app.dependency_overrides[get_api_key] = get_api_key_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Clean up dependency overrides after a test completes
    app.dependency_overrides.clear()
