from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.audio import AudioUploadResponse
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
    db: Annotated[Session, Depends(get_db)]
) -> AudioUploadResponse:
    """Sube un audio con autenticación y lo asocia a un video existente"""
    service = AudioService(db)
    return service.upload_audio_to_video(file, video_id, current_user.id)
