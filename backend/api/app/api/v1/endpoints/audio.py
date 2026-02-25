from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.services.dependencies import get_audio_service
from app.models.user import User
from app.schemas.audio import AudioUploadResponse, AudioURLResponse
from app.services.audio_service import AudioService

router = APIRouter(prefix="/videos", tags=["Audio"])


@router.post(
    "/{video_id}/audio",
    response_model=AudioUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir audio a un video (autenticado)",
    description="Sube un archivo de audio y lo asocia a un video existente (requiere token)",
    responses={
        201: {"description": "Audio subido exitosamente"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"},
        404: {"description": "Video no encontrado"}
    }
)
async def upload_audio_to_video(
    video_id: UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: AudioService = Depends(get_audio_service),
) -> AudioUploadResponse:
    return service.upload_audio_to_video(file, video_id, current_user.id)


@router.get(
    "/audio/{audio_id}/url",
    response_model=AudioURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener URL de descarga del audio",
    description="Genera una URL presignada temporal para descargar el audio desde MinIO",
    responses={
        200: {"description": "URL generada exitosamente"},
        404: {"description": "Audio no encontrado"},
        400: {"description": "Audio sin ruta de almacenamiento"},
    },
)
async def get_audio_url(
    audio_id: UUID,
    service: AudioService = Depends(get_audio_service),
    expires_in: Annotated[
        int,
        Query(
            ge=60,
            le=7 * 24 * 3600,
            description="Tiempo en segundos para que la URL presignada expire (entre 60 y 604800 segundos)"
        )
    ] = 3600
) -> AudioURLResponse:
    return service.get_audio_url(audio_id, expires_in)