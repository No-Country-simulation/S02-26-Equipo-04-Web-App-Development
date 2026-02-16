from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.video import VideoUploadResponse
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video",
    description="Sube un video a MinIO y guarda la metadata",
    responses={
        201: {"description": "Video subido"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"}
    }
)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)]
) -> VideoUploadResponse:
    """Sube un video públicamente (sin autenticación) - Solo para desarrollo"""
    service = VideoService(db)
    return service.upload_video_public(file)


@router.post(
    "/upload/auth",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video (autenticado)",
    description="Sube un video (requiere token) y guarda la metadata",
    responses={
        201: {"description": "Video subido y job encolado"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"}
    }
)
async def upload_video_authenticated(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)]
) -> VideoUploadResponse:
    """Sube un video con autenticación (asociado a usuario)"""
    service = VideoService(db)
    return service.upload_video_authenticated(file, current_user.id)