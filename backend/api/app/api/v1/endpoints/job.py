from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user
from app.database.session import get_db

from app.services.queue_service import QueueService
from app.models.user import User
from app.services.job_service import JobService
from app.services.dependencies import get_job_service
from app.schemas.job import JobReframeResponse, JobStatusResponse, JobReframeRequest

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
        404: {"description": "Video no encontrado"}
    }
)
async def reframe_video(
    video_id: Annotated[UUID, Path(description="ID del Video")],
    body: JobReframeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)]
) -> JobReframeResponse:
    """Crea un nuevo Job de REFRAME para el video subido (requiere autenticación)"""
    return service.reframe_video(
        video_id=video_id,
        user_id=current_user.id,
        start_sec=body.start_sec,
        end_sec=body.end_sec
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
    }
)
async def get_job_status(
    job_id: Annotated[UUID, Path(description="ID del Job")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    service: Annotated[JobService, Depends(get_job_service)]
) -> JobStatusResponse:
    """Devuelve el estado del Job (requiere autenticación)"""
    return service.get_job_status(job_id, current_user.id)