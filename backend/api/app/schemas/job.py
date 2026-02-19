from uuid import UUID
from datetime import datetime
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