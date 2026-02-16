from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, google_oauth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(google_oauth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router)
