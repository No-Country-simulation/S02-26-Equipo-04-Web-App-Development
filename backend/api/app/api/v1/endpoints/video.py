from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.video import VideoUploadResponse, VideoURLResponse
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


@router.get(
    "/{video_id}/url",
    response_model=VideoURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener URL de descarga del video",
    description="Genera una URL presignada temporal para descargar el video desde MinIO",
    responses={
        200: {"description": "URL generada exitosamente"},
        404: {"description": "Video no encontrado"},
        400: {"description": "Video sin ruta de almacenamiento"}
    }
)
async def get_video_url(
    video_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    expires_in: Annotated[int, Query(ge=60, le=86400, description="Tiempo de expiración en segundos (1 min - 24 horas)")] = 3600
) -> VideoURLResponse:
    """Obtiene una URL presignada temporal para descargar el video (expira en 1 hora por defecto)"""
    service = VideoService(db)
    return service.get_video_url(video_id, expires_in)