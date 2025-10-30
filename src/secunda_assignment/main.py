from fastapi import FastAPI, Depends
from secunda_assignment.security import get_api_key
from secunda_assignment.api.v1 import (
    business_categories,
    buildings,
    phone_numbers,
    organizations,
)


API_VERSION = "v1"
app = FastAPI(title="Secunda Assignment API", dependencies=[Depends(get_api_key)])


def include_router(router):
    app.include_router(router, prefix=f"/api/{API_VERSION}")


include_router(phone_numbers.router)
include_router(organizations.router)
include_router(buildings.router)
include_router(business_categories.router)
