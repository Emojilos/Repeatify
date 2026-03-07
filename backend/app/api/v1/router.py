from fastapi import APIRouter

from app.api.v1 import health as health_v1
from app.api.v1 import me, session

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(me.router, tags=["users"])
api_router.include_router(health_v1.router, tags=["health"])
api_router.include_router(session.router, tags=["session"])
