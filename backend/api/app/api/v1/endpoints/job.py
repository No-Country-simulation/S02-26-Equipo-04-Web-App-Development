from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Response, status, Path, Query
from app.core.dependencies import get_current_active_user

from app.models.user import User
from app.models.enums import JobType
from app.services.job_service import JobService
from app.services.dependencies import get_job_service
from app.schemas.job import (
    UserClipDetailResponse,
    JobReframeResponse,
    JobStatusResponse,
    JobReframeRequest,
    JobAutoReframeRequest,
    JobAutoReframeResponse,
    JobAutoReframeResponse2,
    UserClipsResponse,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "/reframe/{video_id}",
    response_model=JobReframeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="New job: video reframe",
    description="Crea un nuevo Job de REFRAME",
    responses={
        201: {"description": "Job creado"},
        400: {"description": "Archivo inválido"},
        401: {"description": "No autenticado"},
        404: {"description": "Video no encontrado"},
    },
)
async def reframe_video(
    video_id: Annotated[UUID, Path(description="ID del Video")],
    body: JobReframeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobReframeResponse:
    """Crea un nuevo Job de REFRAME para el video subido (requiere autenticación)"""
    return service.reframe_video(
        video_id=video_id,
        user_id=current_user.id,
        job_type=JobType.REFRAME,
        start_sec=body.start_sec,
        end_sec=body.end_sec,
        crop_to_vertical=body.crop_to_vertical,
        subtitles=body.subtitles,
        face_tracking=body.face_tracking,
        color_filter=body.color_filter,
        output_style=body.output_style,
        content_profile=body.content_profile,
        watermark=body.watermark
    )


@router.post(
    "/reframe/{video_id}/auto2",
    response_model=JobAutoReframeResponse2,
    status_code=status.HTTP_201_CREATED,
    summary="Generar clips automáticos",
    description="Genera varios jobs REFRAME para clips automáticos de un video",
    responses={
        201: {"description": "Jobs automáticos creados"},
        401: {"description": "No autenticado"},
        404: {"description": "Video no encontrado"},
    },
)
async def auto_reframe_video2(
    video_id: Annotated[UUID, Path(description="ID del Video")],
    body: JobAutoReframeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobAutoReframeResponse2:
    """Crea N jobs automáticos con segmentos sugeridos para shorts"""
    return service.auto_reframe_video2(
        video_id=video_id,
        user_id=current_user.id,
        job_type=JobType.AUTO_REFRAME,
        clips_count=body.clips_count,
        clip_duration_sec=body.clip_duration_sec,
        output_style=body.output_style,
        content_profile=body.content_profile,
        watermark=body.watermark
    )


@router.post(
    "/reframe/{video_id}/auto",
    response_model=JobAutoReframeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar clips automáticos",
    description="Genera varios jobs REFRAME para clips automáticos de un video",
    responses={
        201: {"description": "Jobs automáticos creados"},
        401: {"description": "No autenticado"},
        404: {"description": "Video no encontrado"},
    },
)
async def auto_reframe_video(
    video_id: Annotated[UUID, Path(description="ID del Video")],
    body: JobAutoReframeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobAutoReframeResponse:
    """Crea N jobs automáticos con segmentos sugeridos para shorts"""
    return service.auto_reframe_video(
        video_id=video_id,
        user_id=current_user.id,
        clips_count=body.clips_count,
        clip_duration_sec=body.clip_duration_sec,
        output_style=body.output_style,
        content_profile=body.content_profile,
    )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Devuelve el estado del Job",
    description="Devuelve el estado del Job asociado",
    responses={
        200: {"description": "Estado del Job devuelto exitosamente"},
        404: {"description": "Job no encontrado"},
    },
)
async def get_job_status(
    job_id: Annotated[UUID, Path(description="ID del Job")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> JobStatusResponse:
    """Devuelve el estado del Job (requiere autenticación)"""
    return service.get_job_status(job_id, current_user.id)


@router.get(
    "/my-clips",
    response_model=UserClipsResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar mis clips generados",
    description="Devuelve los clips generados por el usuario autenticado",
)
async def get_my_clips(
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[
        str | None, Query(description="Busqueda por nombre de archivo o id de job")
    ] = None,
) -> UserClipsResponse:
    return service.list_user_clips(current_user.id, limit=limit, offset=offset, query=q)


@router.get(
    "/{job_id}",
    response_model=UserClipDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener clip propio",
    description="Devuelve el detalle de un clip (job reframe) del usuario autenticado",
)
async def get_my_clip_by_id(
    job_id: Annotated[UUID, Path(description="ID del clip/job")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> UserClipDetailResponse:
    return service.get_user_clip(job_id, current_user.id)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar clip propio",
    description="Elimina un clip generado (job reframe) del usuario autenticado",
)
async def delete_my_clip(
    job_id: Annotated[UUID, Path(description="ID del clip/job")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)],
) -> Response:
    service.delete_user_clip(job_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
