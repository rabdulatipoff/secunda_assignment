from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from secunda_assignment.storage import schemas
from secunda_assignment.storage.db import get_async_session
from secunda_assignment.storage.repositories import BusinessCategoryRepository
from secunda_assignment.storage.exceptions import (
    BusinessCategoryNotFound,
    BusinessCategoryAlreadyExists,
)


router = APIRouter(prefix=f"/business_categories", tags=["Business Categories"])


def get_business_category_repo(session: AsyncSession = Depends(get_async_session)):
    """Dependency to provide the BusinessCategoryRepository instance."""

    return BusinessCategoryRepository(session=session)


@router.post(
    "/",
    response_model=schemas.BusinessCategoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_business_category(
    business_category: schemas.BusinessCategoryCreate,
    repo: BusinessCategoryRepository = Depends(get_business_category_repo),
):
    """Create a new business category."""

    try:
        db_business_category = await repo.create(
            business_category_schema=business_category
        )
        return db_business_category
    except BusinessCategoryAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business category path already exists",
        )


@router.get("/", response_model=list[schemas.BusinessCategoryRead])
async def get_all_business_categories(
    skip: int = 0,
    limit: int = 100,
    repo: BusinessCategoryRepository = Depends(get_business_category_repo),
):
    """Get all business_categories with pagination."""

    db_orgs = await repo.get_all(skip=skip, limit=limit)
    return db_orgs


@router.get("/{business_category_id}", response_model=schemas.BusinessCategoryRead)
async def get_business_category(
    business_category_id: int,
    repo: BusinessCategoryRepository = Depends(get_business_category_repo),
):
    """Get a specific business_category by its ID."""

    db_business_category = await repo.get_by_id(
        business_category_id=business_category_id
    )
    if db_business_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business category not found"
        )
    return db_business_category


@router.put("/{business_category_id}", response_model=schemas.BusinessCategoryRead)
async def update_business_category(
    business_category_id: int,
    business_category_schema: schemas.BusinessCategoryUpdate,
    repo: BusinessCategoryRepository = Depends(get_business_category_repo),
):
    """Update a business category."""

    try:
        updated_business_category = await repo.update(
            category_id=business_category_id,
            business_category_schema=business_category_schema,
        )
        return updated_business_category
    except BusinessCategoryNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessCategoryAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business category path already exists",
        )


@router.delete("/{business_category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_category(
    business_category_id: int,
    repo: BusinessCategoryRepository = Depends(get_business_category_repo),
):
    """Delete a business category."""

    business_category = await repo.get_by_id(business_category_id=business_category_id)
    if business_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business category not found"
        )

    await repo.delete(business_category)
