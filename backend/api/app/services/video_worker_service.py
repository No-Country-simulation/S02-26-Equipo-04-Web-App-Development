from pathlib import Path
from uuid import UUID, uuid4
from app.core.config import settings

from sqlalchemy import String, cast
from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video

from app.services.queue_service import QueueService
from app.services.storage_service import StorageService
from app.core.logging import setup_logging
from app.utils.exceptions import (
    JobParameterException,
    NotFoundException,
    VideoDBException,
)

logger = setup_logging()

class VideoWorkerService:

    def __init__(self, db: Session):
        self.db = db
    
    def update_status(
            
        self,
        job_id: UUID,
        status: JobStatus,
        error_message: str | None = None,
        output_path: str | None = None
    ) -> bool:
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.warning(f"❌ Job {job_id} not found in DB for status update")
                return False

            job.status = status

            if error_message is not None:
                job.error_message = error_message

            if output_path is not None:
                job.output_path = output_path

            self.db.commit()
            return True

        except Exception as exc:
            self.db.rollback()
            logger.error(f"❌ Could not persist state for job {job_id}: {exc}")
            return False
        

    def get_by_id(self, job_id: UUID) -> Job | None:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundException("Job not found")
        return job