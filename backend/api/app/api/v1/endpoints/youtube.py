"""
Endpoints para publicación de videos en YouTube.

Controlador limpio: solo gestiona las llamadas al servicio
y devuelve respuestas HTTP. Toda la lógica de negocio vive
en ``YouTubeUploadService``.
"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.youtube import (
    YouTubeConnectionStatus,
    YouTubeMetadataSuggestionResponse,
    YouTubePublishRequest,
    YouTubePublishResponse,
)
from app.services.dependencies import get_youtube_service
from app.services.youtube_upload_service import YouTubeUploadService

router = APIRouter(prefix="/youtube", tags=["YouTube"])


@router.post(
    "/publish/{job_id}",
    response_model=YouTubePublishResponse,
    status_code=status.HTTP_200_OK,
    summary="Publicar clip procesado en YouTube",
    description=(
        "Publica un clip procesado (Job con estado DONE) en el canal "
        "de YouTube del usuario autenticado."
    ),
    responses={
        200: {"description": "Video publicado exitosamente"},
        400: {"description": "Job no apto para publicar o YouTube no conectado"},
        404: {"description": "Job no encontrado"},
    },
)
async def publish_to_youtube(
    job_id: Annotated[UUID, Path(description="ID del Job procesado")],
    body: YouTubePublishRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[YouTubeUploadService, Depends(get_youtube_service)],
) -> YouTubePublishResponse:
    """Publica un clip procesado en YouTube (requiere autenticación)."""
    return await service.publish_job_to_youtube(
        job_id=job_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        privacy=body.privacy,
    )


@router.get(
    "/status",
    response_model=YouTubeConnectionStatus,
    status_code=status.HTTP_200_OK,
    summary="Verificar conexión con YouTube",
    description=(
        "Verifica si el usuario tiene una cuenta de YouTube conectada. "
        "Útil para que el frontend sepa si debe mostrar el botón de "
        "'Conectar YouTube' o 'Publicar en YouTube'."
    ),
    responses={
        200: {"description": "Estado de la conexión de YouTube"},
    },
)
async def check_youtube_connection(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[YouTubeUploadService, Depends(get_youtube_service)],
) -> YouTubeConnectionStatus:
    """Verifica si el usuario tiene cuenta de YouTube conectada."""
    return service.get_connection_status(current_user.id)


@router.get(
    "/metadata/{job_id}",
    response_model=YouTubeMetadataSuggestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Sugerir metadata para YouTube",
    description="Genera titulo, descripcion y hashtags sugeridos para un clip.",
)
async def suggest_metadata(
    job_id: Annotated[UUID, Path(description="ID del Job procesado")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[YouTubeUploadService, Depends(get_youtube_service)],
    tone: Annotated[
        Literal["neutral", "energetic", "informative"],
        Query(description="Tono sugerido para la metadata"),
    ] = "neutral",
) -> YouTubeMetadataSuggestionResponse:
    """Sugiere metadata para publicar un clip en YouTube."""
    return await service.suggest_metadata_for_job(
        job_id=job_id,
        user_id=current_user.id,
        tone=tone,
    )
