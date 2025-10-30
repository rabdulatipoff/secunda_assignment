from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_extra_types.coordinate import Coordinate
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy_utils import Ltree
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape


class BusinessCategoryCreate(BaseModel):
    """Create schema for a new business category."""

    name: str
    path: str
    # Link to existing organizations
    organization_ids: list[int] = []

    @field_validator("path")
    @classmethod
    def validate_path_depth(cls, v: str) -> str:
        """Ensure the Ltree path depth is less than 3."""
        if v:
            depth = len(v.split("."))
            if depth > 3:
                raise ValueError("Category path depth cannot exceed 3 levels")
        return v


class BusinessCategoryUpdate(BaseModel):
    """Update schema for a business category."""

    name: str | None = None
    path: str | None = None
    organization_ids: list[int] | None = None

    @field_validator("path")
    @classmethod
    def validate_path_depth(cls, v: str | None) -> str | None:
        """Ensure the Ltree path depth is less than 3."""
        if v:
            depth = len(v.split("."))
            if depth > 3:
                raise ValueError("Category path depth cannot exceed 3 levels")
        return v


class BusinessCategoryRead(BaseModel):
    """Read schema for a business category."""

    id: int
    name: str
    path: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("path", mode="before")
    @classmethod
    def convert_ltree_path_to_str(cls, v: Any) -> Any:
        if isinstance(v, Ltree):
            return v.path
        return v


class BuildingCreate(BaseModel):
    """Create schema for a new building."""

    address: str
    location: Coordinate


class BuildingUpdate(BaseModel):
    """Update schema for a building."""

    address: str | None = None
    location: Coordinate | None = None


class BuildingRead(BaseModel):
    """Read schema for building information."""

    id: int
    address: str
    location: Coordinate

    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def convert_wkb_to_coordinate(cls, v: Any) -> Any:
        if isinstance(v, WKBElement):
            point = to_shape(v)
            return Coordinate(longitude=point.x, latitude=point.y)
        return v


class PhoneNumberCreate(BaseModel):
    """Create schema for a new phone number.
    Requires an existing organization ID."""

    number: PhoneNumber
    phone_type: str = "main"
    organization_id: int


class PhoneNumberUpdate(BaseModel):
    """Update schema for a phone number."""

    number: PhoneNumber | None = None
    phone_type: str | None = None
    organization_id: int | None = None


class PhoneNumberRead(BaseModel):
    """Read schema for phone number information."""

    id: int
    number: str
    phone_type: str
    organization_id: int

    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    """Create schema for a new organization."""

    name: str
    building_id: int
    phone_number_ids: list[int] = []
    business_category_ids: list[int] = []


class OrganizationUpdate(BaseModel):
    """Update schema for an organization."""

    name: str | None = None
    building_id: int | None = None
    phone_number_ids: list[int] | None = None
    business_category_ids: list[int] | None = None


class OrganizationRead(BaseModel):
    """Read schema for an organization."""

    id: int
    name: str
    building_id: int

    # Link phones and categories
    phone_numbers: list[PhoneNumberRead] = []
    business_categories: list[BusinessCategoryRead] = []

    model_config = ConfigDict(from_attributes=True)


class RadiusQuery(BaseModel):
    center: Coordinate
    radius_meters: float = 100.0  # Default radius is 100 m


class BBoxQuery(BaseModel):
    top_left: Coordinate
    bottom_right: Coordinate
