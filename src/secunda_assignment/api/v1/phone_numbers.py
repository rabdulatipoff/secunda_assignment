from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from secunda_assignment.storage import schemas
from secunda_assignment.storage.db import get_async_session
from secunda_assignment.storage.repositories import PhoneNumberRepository
from secunda_assignment.storage.exceptions import (
    PhoneNumberNotFound,
    OrganizationNotFound,
)


router = APIRouter(prefix=f"/phones", tags=["Phone Numbers"])


def get_phone_number_repo(session: AsyncSession = Depends(get_async_session)):
    """Dependency to provide the PhoneNumberRepository instance."""
    return PhoneNumberRepository(session=session)


@router.post(
    "/", response_model=schemas.PhoneNumberRead, status_code=status.HTTP_201_CREATED
)
async def create_phone_number(
    phone: schemas.PhoneNumberCreate,
    repo: PhoneNumberRepository = Depends(get_phone_number_repo),
):
    """Create a new phone number for an organization."""
    try:
        db_phone = await repo.create(phone_schema=phone)
        return db_phone
    except OrganizationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )


@router.get("/", response_model=list[schemas.PhoneNumberRead])
async def get_all_phone_numbers(
    skip: int = 0,
    limit: int = 100,
    repo: PhoneNumberRepository = Depends(get_phone_number_repo),
):
    """
    Get all phone numbers.
    """
    db_orgs = await repo.get_all(skip=skip, limit=limit)
    return db_orgs


@router.get("/{phone_id}", response_model=schemas.PhoneNumberRead)
async def get_phone_number(
    phone_id: int, repo: PhoneNumberRepository = Depends(get_phone_number_repo)
):
    """
    Get a specific phone number by its ID.
    """
    db_phone = await repo.get_by_id(phone_id=phone_id)
    if db_phone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
        )
    return db_phone


@router.put("/{phone_number_id}", response_model=schemas.PhoneNumberRead)
async def update_phone_number(
    phone_number_id: int,
    phone_number_schema: schemas.PhoneNumberUpdate,
    repo: PhoneNumberRepository = Depends(get_phone_number_repo),
):
    """Update a phone number."""

    try:
        updated_phone_number = await repo.update(
            phone_id=phone_number_id, phone_number_schema=phone_number_schema
        )
        return updated_phone_number
    except PhoneNumberNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{phone_number_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phone_number(
    phone_number_id: int, repo: PhoneNumberRepository = Depends(get_phone_number_repo)
):
    """Delete a phone number."""

    phone_number = await repo.get_by_id(phone_id=phone_number_id)
    if phone_number is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Phone number not found"
        )

    await repo.delete(phone_number)
