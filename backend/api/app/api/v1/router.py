from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, video, audio, job, google_oauth, youtube, facebook_oauth

api_router = APIRouter()

# auth.router ya tiene prefix="/auth" y tags=["Autenticación"]
api_router.include_router(auth.router)
# Google OAuth endpoints bajo /auth/google/
api_router.include_router(google_oauth.router, prefix="/auth", tags=["Autenticación"])
# Facebook OAuth endpoints bajo /auth/facebook/
api_router.include_router(facebook_oauth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(health.router)
api_router.include_router(video.router)
api_router.include_router(audio.router)
api_router.include_router(job.router)
# YouTube publishing endpoints
api_router.include_router(youtube.router)
