from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.video import (
    UpdateVideoRequest,
    ClientVideoMetadata,
    UserVideoDetailResponse,
    UserVideoItem,
    UserVideosResponse,
    VideoUploadResponse,
    VideoURLResponse,
)
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir video (autenticado)",
    description="Sube un video (requiere token) y opcionalmente recibe metadata basica enviada por frontend",
    responses={
        201: {"description": "Video subido exitosamente"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"},
    },
)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    duration_seconds: Annotated[float | None, Form(ge=0)] = None,
    width: Annotated[int | None, Form(ge=1)] = None,
    height: Annotated[int | None, Form(ge=1)] = None,
    fps: Annotated[float | None, Form(ge=0)] = None,
) -> VideoUploadResponse:
    """Sube un video con autenticación (asociado a usuario)"""
    client_metadata = ClientVideoMetadata(
        duration_seconds=(
            max(1, int(round(duration_seconds)))
            if duration_seconds and duration_seconds > 0
            else None
        ),
        width=width,
        height=height,
        fps=max(1, int(round(fps))) if fps and fps > 0 else None,
    )
    service = VideoService(db)
    return service.upload_video_authenticated(
        file,
        current_user.id,
        client_metadata=client_metadata,
    )


@router.get(
    "/{video_id}/url",
    response_model=VideoURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener URL de descarga del video",
    description="Genera una URL presignada temporal para descargar el video desde MinIO",
    responses={
        200: {"description": "URL generada exitosamente"},
        404: {"description": "Video no encontrado"},
        400: {"description": "Video sin ruta de almacenamiento"},
    },
)
async def get_video_url(
    video_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    expires_in: Annotated[
        int,
        Query(
            ge=60,
            le=86400,
            description="Tiempo de expiración en segundos (1 min - 24 horas)",
        ),
    ] = 3600,
) -> VideoURLResponse:
    """Obtiene una URL presignada temporal para descargar el video (expira en 1 hora por defecto)"""
    service = VideoService(db)
    return service.get_video_url(video_id, expires_in)


@router.get(
    "/my-videos",
    response_model=UserVideosResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar mis videos originales",
    description="Devuelve los videos originales subidos por el usuario autenticado",
)
async def get_my_videos(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[
        str | None, Query(description="Busqueda por nombre de archivo o id de video")
    ] = None,
) -> UserVideosResponse:
    service = VideoService(db)
    return service.list_user_videos(
        current_user.id, limit=limit, offset=offset, query=q
    )


@router.get(
    "/{video_id}",
    response_model=UserVideoDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un video propio",
    description="Devuelve metadata y preview del video autenticado",
)
async def get_my_video_by_id(
    video_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserVideoDetailResponse:
    service = VideoService(db)
    return service.get_user_video(video_id, current_user.id)


@router.patch(
    "/{video_id}",
    response_model=UserVideoItem,
    status_code=status.HTTP_200_OK,
    summary="Actualizar metadata de video",
    description="Permite renombrar un video propio",
)
async def update_my_video(
    video_id: UUID,
    body: UpdateVideoRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserVideoItem:
    service = VideoService(db)
    return service.update_user_video(video_id, current_user.id, body)


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar video propio",
    description="Elimina video y metadata asociada del usuario autenticado",
)
async def delete_my_video(
    video_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    service = VideoService(db)
    service.delete_user_video(video_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
