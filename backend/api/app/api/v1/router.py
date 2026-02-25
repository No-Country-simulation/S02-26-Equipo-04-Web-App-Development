from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, video, job, google_oauth, instagram_oauth

api_router = APIRouter()

# auth.router ya tiene prefix="/auth" y tags=["Autenticación"]
api_router.include_router(auth.router)
# Google OAuth endpoints bajo /auth/google/
api_router.include_router(google_oauth.router, prefix="/auth", tags=["Autenticación"])
# Instagram OAuth endpoints bajo /auth/instagram/
api_router.include_router(instagram_oauth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(health.router)
api_router.include_router(video.router)
api_router.include_router(job.router)
