from fastapi import APIRouter

from app import get_settings
from app.api import image_v3, internal

api_v3_router = APIRouter()
api_v3_router.include_router(image_v3.router_v3, tags=["image"])

if get_settings().stage != 'prod':
    internal_router = APIRouter()
    internal_router.include_router(internal.router_internal, tags=["shooter"])
