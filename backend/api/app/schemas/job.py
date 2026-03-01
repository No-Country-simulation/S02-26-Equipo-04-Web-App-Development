from uuid import UUID
from datetime import datetime
from typing import Literal, Any
from pydantic import Field
from app.schemas.base import BaseSchema
from app.models.job import JobStatus, JobType


class JobStatusResponse(BaseSchema):
    job_id: UUID
    status: JobStatus
    output_path: dict[str, Any] | None = None


# ============ REFRAME ============
class JobReframeRequest(BaseSchema):
    start_sec: int = Field(
        gt=0,
        description="Inicio de recorte en Segundo"
    )
    end_sec: int = Field(
        gt=0,
        description="Final del recorte en Segundos"
    )
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
    watermark: str | None = Field(
        default="Hacelo Corto",
        max_length=12,
        description="Opcional: aplicar marca de agua (texto)",
    )


class JobReframeResponse(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    start_sec: int
    end_sec: int
    created_at: datetime


# ============ AUTO REFRAME ============
class JobAutoReframeRequest(BaseSchema):
    clips_count: int | None = Field(
        default=None,
        ge=1,
        le=3,
        description="Cantidad de clips a generar (opcional, backend decide si no se envia)",
    )
    clip_duration_sec: int | None = Field(
        default=None,
        ge=5,
        le=60,
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
    watermark: str | None = Field(
        default="Hacelo Corto",
        max_length=12,
        description="Opcional: aplicar marca de agua (texto)",
    )
    subtitles: bool | None = Field(
        description="Opcional: crear archivo de Subtitulos"
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


# ============ AUTO REFRAME 2 ============
class JobAutoReframeResponse2(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    total_jobs: int
    created_at: datetime


# ============ USER CLIP ============
class UserClipItem(BaseSchema):
    job_id: UUID
    video_id: UUID
    status: JobStatus
    output_path: dict[str, Any] | None = None
    source_filename: str
    created_at: datetime


class UserClipsResponse(BaseSchema):
    total: int
    limit: int
    offset: int
    clips: list[UserClipItem]


class UserClipDetailResponse(BaseSchema):
    clip: UserClipItem

class AutoClipSegment(BaseSchema):
    start_sec: int
    end_sec: int


# ============ ADD AUDIO ============ 
class JobAddAudioRequest(BaseSchema):
    audio_id: UUID
    audio_offset_sec: int = Field(
        ge=0,
        description="Segundo del video donde empieza el audio"
    )

    audio_start_sec: int = Field(
        ge=0,
        description="Inicio del segmento de audio a usar"
    )

    audio_end_sec: int = Field(
        gt=0,
        description="Fin del segmento de audio a usar"
    )

    audio_volume: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Multiplicador de volumen (1.0 = volumen original)"
    )
    #mix_original_audio:
    #fade_in_sec:
    #fade_out_sec:
    #allow_loop:

class JobAddAudioResponse(BaseSchema):
    job_id: UUID
    job_type: JobType
    status: JobStatus
    filename: str
    audio_filename: str
    audio_volume: int
    created_at: datetime