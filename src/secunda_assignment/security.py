import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
API_KEY = os.getenv("APP_API_KEY")


async def get_api_key(key: str = Security(api_key_header)):
    """
    Dependency to validate the static API key.

    Reads the key from the 'X-API-KEY' header and compares it
    to the key set in the environment.
    """
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured by the server",
        )

    if key and secrets.compare_digest(key, API_KEY):
        return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )
