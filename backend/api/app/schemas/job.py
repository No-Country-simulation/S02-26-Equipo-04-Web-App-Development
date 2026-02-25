from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import Field
from app.schemas.base import BaseSchema
from app.models.job import JobStatus, JobType


class JobReframeResponse(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    start_sec: int
    end_sec: int
    created_at: datetime


class JobStatusResponse(BaseSchema):
    job_id: UUID
    status: JobStatus
    output_path: str | None = None


class JobReframeRequest(BaseSchema):
    start_sec: int = Field(..., description="Inicio de recorte en Segundo")
    end_sec: int = Field(..., description="Final del recorte en Segundos")
    job_type: JobType = Field(
        default=JobType.REFRAME,
    )
    crop_to_vertical: bool | None = Field(
        default=None,
        description="Opcional: forzar salida vertical",
    )
    subtitles: bool | None = Field(
        default=None,
        description="Opcional: habilitar subtitulos",
    )
    face_tracking: bool | None = Field(
        default=None,
        description="Opcional: seguimiento facial",
    )
    color_filter: bool | None = Field(
        default=None,
        description="Opcional: aplicar filtro de color",
    )
    output_style: Literal["vertical", "speaker_split"] = Field(
        default="vertical",
        description="Estilo de salida: vertical clasico o split speaker",
    )
    content_profile: Literal["auto", "interview", "sports", "music"] = Field(
        default="auto",
        description="Perfil de contenido para ajustar framing (auto/entrevista/deportes/musica)",
    )


class AutoClipSegment(BaseSchema):
    start_sec: int
    end_sec: int


class JobAutoReframeRequest(BaseSchema):
    clips_count: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Cantidad de clips a generar (opcional, backend decide si no se envia)",
    )
    clip_duration_sec: int | None = Field(
        default=None,
        ge=5,
        le=120,
        description="Duracion por clip (opcional, backend decide si no se envia)",
    )
    output_style: Literal["vertical", "speaker_split"] = Field(
        default="vertical",
        description="Estilo de salida para los clips automaticos",
    )
    content_profile: Literal["auto", "interview", "sports", "music"] = Field(
        default="auto",
        description="Perfil de contenido para ajustar framing (auto/entrevista/deportes/musica)",
    )


class JobAutoReframeItem(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    start_sec: int
    end_sec: int
    created_at: datetime


class JobAutoReframeResponse(BaseSchema):
    video_id: UUID
    total_jobs: int
    clip_duration_sec: int
    used_video_duration_sec: int | None = None
    jobs: list[JobAutoReframeItem]


class JobAutoReframeResponse2(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    total_jobs: int
    created_at: datetime
    

class UserClipItem(BaseSchema):
    job_id: UUID
    video_id: UUID
    status: JobStatus
    output_path: str | None = None
    source_filename: str
    created_at: datetime


class UserClipsResponse(BaseSchema):
    total: int
    limit: int
    offset: int
    clips: list[UserClipItem]


class UserClipDetailResponse(BaseSchema):
    clip: UserClipItem
