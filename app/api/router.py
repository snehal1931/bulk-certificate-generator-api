"""Main API router combining all versions."""

from fastapi import APIRouter
from app.api.v1 import api_v1_router

main_router = APIRouter(prefix="/api")
main_router.include_router(api_v1_router)
