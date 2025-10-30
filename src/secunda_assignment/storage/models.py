from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import LtreeType
from geoalchemy2 import Geometry


app_metadata = sa.MetaData()


class Base(DeclarativeBase):
    metadata = app_metadata


organization_business_category = sa.Table(
    "organization_business_category",
    Base.metadata,
    sa.Column("organization_id", sa.ForeignKey("organization.id")),
    sa.Column("category_id", sa.ForeignKey("business_category.id")),
)


class BusinessCategory(Base):
    __tablename__ = "business_category"
    __table_args__ = (
        sa.Index("ix_business_category_path_gist", "path", postgresql_using="gist"),
        # Set maximum path depth of 3 elements
        sa.CheckConstraint("nlevel(path) <= 3", name="ck_business_category_path_depth"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    path: Mapped[str] = mapped_column(LtreeType, unique=True, nullable=False)
    organizations: Mapped[list[Organization]] = relationship(
        secondary=organization_business_category, back_populates="business_categories"
    )


class Building(Base):
    __tablename__ = "building"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    organizations: Mapped[list[Organization]] = relationship(back_populates="building")


class PhoneNumber(Base):
    __tablename__ = "phone_number"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(sa.String(30), nullable=False)
    phone_type: Mapped[str] = mapped_column(sa.String(30), nullable=True)
    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organization.id"), nullable=False
    )
    organization: Mapped[Organization] = relationship(back_populates="phone_numbers")


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(255), index=True)
    building_id: Mapped[int] = mapped_column(
        sa.ForeignKey("building.id"), nullable=False
    )
    phone_numbers: Mapped[list[PhoneNumber]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", lazy="selectin"
    )
    building: Mapped[Building] = relationship(back_populates="organizations")
    business_categories: Mapped[list[BusinessCategory]] = relationship(
        secondary=organization_business_category,
        back_populates="organizations",
        lazy="selectin",
    )
