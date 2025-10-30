from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from secunda_assignment.storage import schemas
from secunda_assignment.storage.db import get_async_session
from secunda_assignment.storage.repositories import BuildingRepository
from secunda_assignment.storage.exceptions import BuildingNotFound, AddressAlreadyExists


router = APIRouter(prefix=f"/buildings", tags=["Buildings"])


def get_building_repo(session: AsyncSession = Depends(get_async_session)):
    """Dependency to provide the BuildingRepository instance."""
    return BuildingRepository(session=session)


@router.post(
    "/", response_model=schemas.BuildingRead, status_code=status.HTTP_201_CREATED
)
async def create_building(
    building: schemas.BuildingCreate,
    repo: BuildingRepository = Depends(get_building_repo),
):
    """Create a new building."""
    try:
        db_building = await repo.create(building_schema=building)
        return db_building
    except AddressAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Building address already exists",
        )


@router.get("/", response_model=list[schemas.BuildingRead])
async def get_all_buildings(
    skip: int = 0,
    limit: int = 100,
    repo: BuildingRepository = Depends(get_building_repo),
):
    """
    Get all buildings.
    """
    db_orgs = await repo.get_all(skip=skip, limit=limit)
    return db_orgs


@router.get("/{building_id}", response_model=schemas.BuildingRead)
async def get_building(
    building_id: int, repo: BuildingRepository = Depends(get_building_repo)
):
    """
    Get a specific building by its ID.
    """
    db_building = await repo.get_by_id(building_id=building_id)
    if db_building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return db_building


@router.put("/{building_id}", response_model=schemas.BuildingRead)
async def update_building(
    building_id: int,
    building_schema: schemas.BuildingUpdate,
    repo: BuildingRepository = Depends(get_building_repo),
):
    """Update an building."""

    try:
        updated_building = await repo.update(
            building_id=building_id, building_schema=building_schema
        )
        return updated_building
    except BuildingNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AddressAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Building address already exists",
        )


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_building(
    building_id: int, repo: BuildingRepository = Depends(get_building_repo)
):
    """Delete an building."""

    building = await repo.get_by_id(building_id=building_id)
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )

    await repo.delete(building)


@router.post("/find/radius", response_model=list[schemas.BuildingRead])
async def find_buildings_in_radius(
    query: schemas.RadiusQuery,
    repo: BuildingRepository = Depends(get_building_repo),
):
    """Find buildings within a given radius (m)."""

    buildings = await repo.find_in_radius(
        center=query.center, radius_meters=query.radius_meters
    )
    return buildings


@router.post("/find/bbox", response_model=list[schemas.BuildingRead])
async def find_buildings_in_bounding_box(
    query: schemas.BBoxQuery,
    repo: BuildingRepository = Depends(get_building_repo),
):
    """Find buildings within a bounding box defined by two points."""

    buildings = await repo.find_in_bbox(
        top_left=query.top_left, bottom_right=query.bottom_right
    )
    return buildings
