from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, video, job

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(video.router)
api_router.include_router(job.router)
