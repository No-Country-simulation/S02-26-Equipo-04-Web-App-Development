from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, google_oauth

api_router = APIRouter()

# auth.router ya tiene prefix="/auth" y tags=["Autenticación"]
api_router.include_router(auth.router)
# Google OAuth endpoints bajo /auth/google/
api_router.include_router(google_oauth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(health.router)
