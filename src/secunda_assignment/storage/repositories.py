# secunda_assignment/storage/repositories.py

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_utils import Ltree
from geoalchemy2 import Geography
from pydantic_extra_types.coordinate import Coordinate
from secunda_assignment.storage import schemas
from secunda_assignment.storage.models import (
    Organization,
    Building,
    PhoneNumber,
    BusinessCategory,
)
from secunda_assignment.storage.exceptions import (
    BusinessCategoryNotFound,
    PhoneNumberNotFound,
    BuildingNotFound,
    OrganizationNotFound,
    AddressAlreadyExists,
    BusinessCategoryAlreadyExists,
    OrganizationsStillExist,
)


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


class BusinessCategoryRepository(BaseRepository):
    async def create(
        self, business_category_schema: schemas.BusinessCategoryCreate
    ) -> BusinessCategory:
        """Create a new business category and link organizations by IDs."""

        category_data = business_category_schema.model_dump()
        organization_ids = category_data.pop("organization_ids")
        business_category_path = Ltree(category_data.pop("path"))

        # Check if the category path already exists
        statement = select(BusinessCategory).where(
            BusinessCategory.path == business_category_path
        )
        result = (await self.session.execute(statement)).scalar_one_or_none()
        if result is not None:
            raise BusinessCategoryAlreadyExists

        db_category = BusinessCategory(path=business_category_path, **category_data)

        if organization_ids:
            statement = select(Organization).where(
                Organization.id.in_(organization_ids)
            )
            result = await self.session.execute(statement)
            db_category.organizations = list(result.scalars().all())

        self.session.add(db_category)
        await self.session.commit()
        await self.session.refresh(db_category)
        return db_category

    async def get_by_id(self, business_category_id: int) -> BusinessCategory | None:
        """Get a business category by its ID."""

        statement = select(BusinessCategory).where(
            BusinessCategory.id == business_category_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_path(self, business_category_path: int) -> BusinessCategory | None:
        """Get a business category by its path."""

        statement = select(BusinessCategory).where(
            BusinessCategory.path == Ltree(business_category_path)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[BusinessCategory]:
        """Get all business categories with pagination."""

        statement = select(BusinessCategory).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self,
        category_id: int,
        business_category_schema: schemas.BusinessCategoryUpdate,
    ) -> BusinessCategory:
        """Update an existing business category."""

        db_category = await self.get_by_id(business_category_id=category_id)
        if not db_category:
            raise BusinessCategoryNotFound

        update_data = business_category_schema.model_dump(exclude_unset=True)

        if "path" in update_data:
            ltree_path = Ltree(update_data.pop("path"))

            # Check if the path already exists, excluding self
            statement = select(BusinessCategory).where(
                BusinessCategory.path == ltree_path,
                BusinessCategory.id != category_id,
            )
            result = (await self.session.execute(statement)).scalar_one_or_none()
            if result:
                raise BusinessCategoryAlreadyExists

            db_category.path = ltree_path.path

        if "organization_ids" in update_data:
            org_ids = update_data.pop("organization_ids")

            org_statement = select(Organization).where(Organization.id.in_(org_ids))
            result = await self.session.execute(org_statement)

            db_category.organizations = list(result.scalars().all())

        for k, v in update_data.items():
            setattr(db_category, k, v)

        self.session.add(db_category)
        await self.session.commit()
        await self.session.refresh(db_category)
        return db_category

    async def delete(self, db_category: BusinessCategory) -> None:
        """Delete a business category."""

        await self.session.delete(db_category)
        await self.session.commit()


class BuildingRepository(BaseRepository):
    async def create(self, building_schema: schemas.BuildingCreate) -> Building:
        """Create a new building."""

        building_data = building_schema.model_dump()
        location_coord = building_data.pop("location")
        address = building_data.get("address")

        # Check if the address already exists
        statement = select(Building).where(Building.address == address)
        result = (await self.session.execute(statement)).scalar_one_or_none()
        if result is not None:
            raise AddressAlreadyExists

        # Convert Coordinate to PostGIS WKT string
        location_wkt = f"SRID=4326;POINT({location_coord['longitude']} {location_coord['latitude']})"

        # Create the building with specified location
        db_building = Building(**building_data, location=location_wkt)

        self.session.add(db_building)
        await self.session.commit()
        await self.session.refresh(db_building)
        return db_building

    async def get_by_id(self, building_id: int) -> Building | None:
        """Get a building by its ID."""

        statement = select(Building).where(Building.id == building_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Building]:
        """Get all buildings with pagination."""

        statement = select(Building).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, building_id: int, building_schema: schemas.BuildingUpdate
    ) -> Building:
        """Update an existing building info."""

        db_building = await self.get_by_id(building_id=building_id)
        if not db_building:
            raise BuildingNotFound

        update_data = building_schema.model_dump(exclude_unset=True)

        if "address" in update_data:
            new_address = update_data.pop("address")

            # Check if address already exists, excluding self
            statement = select(Building).where(
                Building.address == new_address, Building.id != building_id
            )
            result = (await self.session.execute(statement)).scalar_one_or_none()
            if result:
                raise AddressAlreadyExists

            db_building.address = new_address

        if "location" in update_data:
            point = update_data.pop("location")

            db_building.location = (
                f"SRID=4326;POINT({point['longitude']} {point['latitude']})"
            )

        for k, v in update_data.items():
            setattr(db_building, k, v)

        self.session.add(db_building)
        await self.session.commit()
        await self.session.refresh(db_building)
        return db_building

    async def delete(self, db_building: Building) -> None:
        """Delete a building. Fail if organizations are still linked."""
        try:
            await self.session.delete(db_building)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise OrganizationsStillExist

    async def find_in_radius(
        self, center: Coordinate, radius_meters: float
    ) -> list[Building]:
        """Find buildings within a given radius (m)."""

        point = func.ST_GeographyFromText(
            f"SRID=4326;POINT({center.longitude} {center.latitude})"
        )
        statement = select(Building).where(
            func.ST_DWithin(Building.location.cast(Geography()), point, radius_meters)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_in_bbox(
        self, top_left: Coordinate, bottom_right: Coordinate
    ) -> list[Building]:
        """Find buildings within a bounding box defined by 2 points."""

        # ST_MakeEnvelope goes bottom left to top right
        envelope = func.ST_MakeEnvelope(
            top_left.longitude,
            bottom_right.latitude,
            bottom_right.longitude,
            top_left.latitude,
            4326,
        )
        statement = select(Building).where(
            func.ST_Intersects(Building.location, envelope)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


class PhoneNumberRepository(BaseRepository):
    async def create(self, phone_schema: schemas.PhoneNumberCreate) -> PhoneNumber:
        """
        Create a new phone number for a given organization ID.
        """
        phone_data = phone_schema.model_dump()
        org_id = phone_data.pop("organization_id")

        # Check if organization exists
        statement = select(Organization).where(Organization.id == org_id)
        result = (await self.session.execute(statement)).scalar_one_or_none()
        if not result:
            raise OrganizationNotFound

        db_phone = PhoneNumber(organization_id=org_id, **phone_data)
        self.session.add(db_phone)
        await self.session.commit()
        await self.session.refresh(db_phone)
        return db_phone

    async def get_by_id(self, phone_id: int) -> PhoneNumber | None:
        """Get a phone number by its ID."""

        statement = select(PhoneNumber).where(PhoneNumber.id == phone_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[PhoneNumber]:
        """Get all phone numbers with pagination."""

        statement = select(PhoneNumber).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, phone_id: int, phone_number_schema: schemas.PhoneNumberUpdate
    ) -> PhoneNumber:
        """Update an existing phone number."""

        db_phone = await self.get_by_id(phone_id=phone_id)
        if not db_phone:
            raise PhoneNumberNotFound

        update_data = phone_number_schema.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_phone, k, v)

        self.session.add(db_phone)
        await self.session.commit()
        await self.session.refresh(db_phone)
        return db_phone

    async def delete(self, db_phone: PhoneNumber) -> None:
        """Delete a phone number."""

        await self.session.delete(db_phone)
        await self.session.commit()


class OrganizationRepository(BaseRepository):
    async def create(self, org_schema: schemas.OrganizationCreate) -> Organization:
        """Create a new organization and its relationships."""

        org_data = org_schema.model_dump()
        phone_number_ids = org_data.pop("phone_number_ids")
        category_ids = org_data.pop("business_category_ids")
        building_id = org_data.get("building_id")

        # Check if building exists
        statement = select(Building).where(Building.id == building_id)
        result = (await self.session.execute(statement)).scalar_one_or_none()
        if not result:
            raise BuildingNotFound

        categories = []
        if category_ids:
            statement = select(BusinessCategory).where(
                BusinessCategory.id.in_(category_ids)
            )
            result = await self.session.execute(statement)
            categories = result.scalars().all()

        phone_numbers = []
        if phone_number_ids:
            statement = select(PhoneNumber).where(PhoneNumber.id.in_(phone_number_ids))
            result = await self.session.execute(statement)
            phone_numbers = result.scalars().all()

        db_org = Organization(**org_data)

        db_org.business_categories = list(categories)
        db_org.phone_numbers = list(phone_numbers)

        self.session.add(db_org)
        await self.session.commit()
        await self.session.refresh(db_org)
        return db_org

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Organization]:
        """Get all organizations with pagination."""

        statement = select(Organization).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, org_id: int) -> Organization | None:
        """Get an organization by its ID."""

        statement = select(Organization).where(Organization.id == org_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Organization | None:
        """Get an organization by its exact name."""

        statement = select(Organization).where(Organization.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_building_id(self, building_id: int) -> list[Organization]:
        """Get all organizations for a given building ID."""

        statement = select(Organization).where(Organization.building_id == building_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update(
        self, org_id: int, org_schema: schemas.OrganizationUpdate
    ) -> Organization:
        """Update an existing organization."""

        # Check if the organization exists
        db_org = await self.get_by_id(org_id=org_id)
        if not db_org:
            raise OrganizationNotFound

        update_data = org_schema.model_dump(exclude_unset=True)

        if "building_id" in update_data:
            building_id = update_data["building_id"]

            # Check if the building exists
            statement = select(Building).where(Building.id == building_id)
            result = (await self.session.execute(statement)).scalar_one_or_none()
            if not result:
                raise BuildingNotFound

            db_org.building_id = building_id

        if "business_category_ids" in update_data:
            cat_ids = update_data.pop("business_category_ids")

            statement = select(BusinessCategory).where(BusinessCategory.id.in_(cat_ids))
            result = await self.session.execute(statement)

            db_org.business_categories = list(result.scalars().all())

        if "phone_number_ids" in update_data:
            phone_ids = update_data.pop("phone_number_ids")

            statement = select(PhoneNumber).where(PhoneNumber.id.in_(phone_ids))
            result = await self.session.execute(statement)

            db_org.phone_numbers = list(result.scalars().all())

        for k, v in update_data.items():
            setattr(db_org, k, v)

        self.session.add(db_org)
        await self.session.commit()
        await self.session.refresh(db_org)
        return db_org

    async def delete(self, db_org: Organization) -> None:
        """Delete an organization with its phone numbers."""
        await self.session.delete(db_org)
        await self.session.commit()

    async def find_in_radius(
        self, center: Coordinate, radius_meters: float
    ) -> list[Organization]:
        """Find organizations within a given radius (m)."""

        point = func.ST_GeographyFromText(
            f"SRID=4326;POINT({center.longitude} {center.latitude})"
        )
        statement = (
            select(Organization)
            .join(Building)
            .where(
                func.ST_DWithin(
                    Building.location.cast(Geography()), point, radius_meters
                )
            )
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def find_in_bbox(
        self, top_left: Coordinate, bottom_right: Coordinate
    ) -> list[Organization]:
        """Find organizations within a bounding box defined by 2 points."""

        # ST_MakeEnvelope goes bottom left to top right
        envelope = func.ST_MakeEnvelope(
            top_left.longitude,
            bottom_right.latitude,
            bottom_right.longitude,
            top_left.latitude,
            4326,
        )
        statement = (
            select(Organization)
            .join(Building)
            .where(func.ST_Intersects(Building.location, envelope))
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_category_path(self, path: str) -> list[Organization]:
        """Get organizations matching an Ltree category path and all sub-categories."""

        ltree_path = Ltree(path)

        statement = (
            select(Organization)
            .join(Organization.business_categories)
            .where(BusinessCategory.path.op("<@")(ltree_path))
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())
