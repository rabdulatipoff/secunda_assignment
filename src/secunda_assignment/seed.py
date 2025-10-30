import asyncio
import logging
from pydantic_extra_types.coordinate import Coordinate, Longitude, Latitude
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import Ltree

from secunda_assignment.storage.db import async_session_maker, engine
from secunda_assignment.storage.models import (
    Base,
    BusinessCategory,
    Building,
    PhoneNumber,
    Organization,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(drop: bool = True):
    """Create all tables (optionally drop before creation)."""

    connection = async_session_maker().bind
    async with connection.begin() as conn:
        if drop:
            logger.info("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully!")


async def seed_data():
    """Populate the database with sample data."""

    await init_db()

    async with async_session_maker() as session:
        try:
            logger.info("Seeding buildings...")

            coords = [
                Coordinate(longitude=Longitude(lon), latitude=Latitude(lat))
                for lon, lat in (
                    (55.694296, 37.496675),
                    (55.690246, 37.490337),
                    (55.692614, 37.494852),
                    (55.694271, 37.504111),
                    (55.691169, 37.492733),
                )
            ]
            buildings = [
                Building(
                    address=addr,
                    location=f"SRID=4326;POINT({coords[i].longitude} {coords[i].latitude})",
                )
                for i, addr in enumerate(
                    (
                        "Мичуринский проспект, 31 к. 4",
                        "Улица Раменки, 16",
                        "Улица Раменки, 5",
                        "Мичуринский проспект, 1, 1 этаж",
                        "Улица Раменки, 19",
                    )
                )
            ]
            session.add_all(buildings)

            logger.info("Seeding business categories...")

            c_food = BusinessCategory(name="Food", path=Ltree("food"))
            c_fast_food = BusinessCategory(name="Fast Food", path=Ltree("food.fast"))
            c_pizza = BusinessCategory(name="Pizza", path=Ltree("food.fast.pizza"))
            c_grocery = BusinessCategory(name="Grocery", path=Ltree("food.grocery"))
            c_restaurant = BusinessCategory(
                name="Restaurant", path=Ltree("food.restaurant")
            )

            c_services = BusinessCategory(name="Services", path=Ltree("services"))
            c_repairs = BusinessCategory(name="Repairs", path=Ltree("services.repairs"))

            c_recreation = BusinessCategory(name="Recreation", path=Ltree("recreation"))
            c_sports = BusinessCategory(name="Sports", path=Ltree("recreation.sports"))

            c_retail = BusinessCategory(name="Retail", path=Ltree("retail"))
            c_books = BusinessCategory(name="Books", path=Ltree("retail.books"))
            c_clothes = BusinessCategory(name="Clothes", path=Ltree("retail.clothes"))
            c_tools = BusinessCategory(name="Tools", path=Ltree("retail.tools"))
            session.add_all(
                [
                    c_food,
                    c_fast_food,
                    c_pizza,
                    c_grocery,
                    c_restaurant,
                    c_services,
                    c_repairs,
                    c_recreation,
                    c_sports,
                    c_retail,
                    c_books,
                    c_clothes,
                    c_tools,
                ]
            )

            logger.info("Seeding organizations...")

            org1 = Organization(
                name="Белый Кролик",
                building=buildings[0],
                phone_numbers=[
                    PhoneNumber(number="tel:+7-499-653-63-59", phone_type="main"),
                ],
                business_categories=[c_retail, c_books],
            )

            org2 = Organization(
                name="Сервисный центр",
                building=buildings[0],
                phone_numbers=[
                    PhoneNumber(number="tel:+7-495-761-73-73", phone_type="main"),
                    PhoneNumber(number="tel:+7-495-761-73-74", phone_type="backup"),
                ],
                business_categories=[c_services, c_repairs],
            )

            org3 = Organization(
                name="Дикси",
                building=buildings[1],
                phone_numbers=[
                    PhoneNumber(number="tel:+7-800-101-10-01", phone_type="hotline"),
                ],
                business_categories=[c_grocery],
            )

            org4 = Organization(
                name="Нидия",
                building=buildings[1],
                phone_numbers=[
                    PhoneNumber(number="tel:+7-495-931-83-61", phone_type="main"),
                ],
                business_categories=[c_clothes],
            )

            org5 = Organization(
                name="Строймир",
                building=buildings[1],
                business_categories=[c_tools],
            )

            org6 = Organization(
                name="Чайхона АЗИЯ ХАЛЯЛЬ",
                building=buildings[2],
                phone_numbers=[
                    PhoneNumber(number="+7-925-433-30-06", phone_type="main"),
                ],
                business_categories=[c_restaurant],
            )

            org7 = Organization(
                name="Папа Джонс",
                building=buildings[3],
                phone_numbers=[
                    PhoneNumber(number="+7-964-628-63-14", phone_type="main"),
                ],
                business_categories=[c_fast_food, c_pizza],
            )

            org8 = Organization(
                name='Спортивный комплекс "Раменки"',
                building=buildings[4],
                phone_numbers=[
                    PhoneNumber(
                        number="tel:+7-499-444-14-78", phone_type="headquarters"
                    ),
                    PhoneNumber(
                        number="tel:+7-499-444-14-78 add. 6170", phone_type="office"
                    ),
                ],
                business_categories=[c_sports],
            )

            session.add_all([org1, org2, org3, org4, org5, org6, org7, org8])

            await session.commit()
            logger.info("Successfully seeded database!")

        except IntegrityError as e:
            await session.rollback()
            logger.error(f"ERROR: Seeding failed due to an integrity constraint: {e}")
        except Exception as e:
            await session.rollback()
            logger.error(f"ERROR: An unexpected error occurred: {e}")
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
