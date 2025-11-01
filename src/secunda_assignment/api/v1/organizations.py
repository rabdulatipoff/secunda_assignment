from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from secunda_assignment.storage import schemas
from secunda_assignment.storage.db import get_async_session
from secunda_assignment.storage.repositories import OrganizationRepository
from secunda_assignment.storage.exceptions import BuildingNotFound, OrganizationNotFound


router = APIRouter(prefix=f"/organizations", tags=["Organizations"])


def get_organization_repo(session: AsyncSession = Depends(get_async_session)):
    """Dependency to provide the OrganizationRepository instance."""

    return OrganizationRepository(session=session)


@router.post(
    "/", response_model=schemas.OrganizationRead, status_code=status.HTTP_201_CREATED
)
async def create_organization(
    org_schema: schemas.OrganizationCreate,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Create a new organization."""

    try:
        org = await repo.create(org_schema=org_schema)
        return org
    except BuildingNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )


@router.get("/", response_model=list[schemas.OrganizationRead])
async def get_all_organizations(
    skip: int = 0,
    limit: int = 100,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Get all organizations with pagination."""

    orgs = await repo.get_all(skip=skip, limit=limit)
    return orgs


@router.get("/by-name", response_model=schemas.OrganizationRead)
async def get_organization_by_name(
    name: str = Query(..., description="Exact organization name"),
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Get an organization by its exact name."""

    org = await repo.get_by_name(name=name)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


@router.get("/by-building/{building_id}", response_model=list[schemas.OrganizationRead])
async def get_organizations_by_building(
    building_id: int,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Get all organizations located in a building given by its ID."""

    orgs = await repo.get_by_building_id(building_id=building_id)
    return orgs


@router.get("/by-category", response_model=list[schemas.OrganizationRead])
async def get_organizations_by_category(
    path: str = Query(
        ..., description="Ltree path (e.g. 'food.fast.pizza')", example="food"
    ),
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Get organizations matching a category path and all its sub-categories."""

    organizations = await repo.get_by_category_path(path=path)
    return organizations


@router.get("/{org_id}", response_model=schemas.OrganizationRead)
async def get_organization(
    org_id: int, repo: OrganizationRepository = Depends(get_organization_repo)
):
    """Get a specific organization by its ID."""

    org = await repo.get_by_id(org_id=org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


@router.put("/{org_id}", response_model=schemas.OrganizationRead)
async def update_organization(
    org_id: int,
    org_schema: schemas.OrganizationUpdate,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Update an organization."""

    try:
        updated_org = await repo.update(org_id=org_id, org_schema=org_schema)
        return updated_org
    except (OrganizationNotFound, BuildingNotFound) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int, repo: OrganizationRepository = Depends(get_organization_repo)
):
    """Delete an organization."""

    org = await repo.get_by_id(org_id=org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    await repo.delete(org)


@router.post("/find/radius", response_model=list[schemas.OrganizationRead])
async def find_organizations_in_radius(
    query: schemas.RadiusQuery,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Find organizations within a given radius (m)."""

    orgs = await repo.find_in_radius(
        center=query.center, radius_meters=query.radius_meters
    )
    return orgs


@router.post("/find/bbox", response_model=list[schemas.OrganizationRead])
async def find_organizations_in_bounding_box(
    query: schemas.BBoxQuery,
    repo: OrganizationRepository = Depends(get_organization_repo),
):
    """Find organizations within a bounding box defined by two points."""

    orgs = await repo.find_in_bbox(
        top_left=query.top_left, bottom_right=query.bottom_right
    )
    return orgs
