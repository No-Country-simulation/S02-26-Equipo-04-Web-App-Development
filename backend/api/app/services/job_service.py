from uuid import UUID, uuid4
from datetime import datetime
from venv import logger
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video
from app.schemas.job import JobReframeResponse, JobStatusResponse
from app.services.queue_service import QueueService
from app.utils.exceptions import (
    JobParameterException,
    NotFoundException,
)


class JobService:
    """Servicio de Jobs - Persiste un Job, luego envia mensaje a Redis"""
    
    def __init__(self, db: Session, queue: QueueService):
        self.db = db
        self.queue = queue
    

    def get_job_status(self, job_id: UUID, user_id: UUID) -> JobStatusResponse:
        job = (
        self.db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == user_id
        )
        .first()
        )

        if not job:
            raise NotFoundException("Job Not found")

        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            output_path=job.output_path
        )
    
    
    def reframe_video(self, video_id: UUID, user_id: UUID, start_sec: int, end_sec: int) -> JobReframeResponse:
        video = (
            self.db.query(Video)
            .filter(
                Video.id == video_id,
                Video.user_id == user_id
            )
            .first()
        )

        if not video:
            raise NotFoundException("Video not found"
            )
        
        # ...TODO, tabla videos no guarda duracion?
        # validar que start y end sec sean coherentes con la duracion del video
        #video_total_sec = video.duration_seconds
        #if video_total_sec is None:
        #    raise JobParameterException("Video duration not available")
        #if start_sec < 0 or start_sec > video_total_sec or end_sec > video_total_sec:
        #    raise JobParameterException()
        if start_sec < 0 or start_sec > end_sec:
            raise JobParameterException()

        # validar que no exista ya un job PENDING/RUNNING/FAILED para ese video_id
        existing_job = (
            self.db.query(Job)
            .filter(
                Job.video_id == video_id,
                Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED])
            )
            .first()
        )

        if existing_job:
            if existing_job.status == JobStatus.RUNNING:
                logger.info(f"Existing job {existing_job.id} is already {existing_job.status}")
                return JobReframeResponse(
                    job_id=existing_job.id,
                    job_type=existing_job.job_type,
                    status=existing_job.status,
                    filename=video.original_filename,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    created_at=existing_job.created_at
                )

        if existing_job:
            logger.info(f"Existing job {existing_job.id} found for video {video_id} with status {existing_job.status}, reusing it")
            # republicar a Redis
            try:
                self.queue.publish_reframe_job(
                    job_id=str(existing_job.id),
                    video_id=str(video_id),
                    user_id=str(user_id),
                    start_sec=start_sec,
                    end_sec=end_sec,
                )
            except Exception as e:
                # Si falla Redis, dejamos el job en FAILED
                existing_job.status = JobStatus.FAILED
                existing_job.error_message = "Error enviando job a la cola"
                self.db.commit()
                raise e
    
            return JobReframeResponse(
                job_id=existing_job.id,
                job_type=existing_job.job_type,
                status=existing_job.status,
                filename=video.original_filename,
                start_sec=start_sec,
                end_sec=end_sec,
                created_at=existing_job.created_at
            )

        # crear Job en DB
        job = Job(
            user_id=user_id,
            video_id=video_id,
            job_type=JobType.REFRAME,
            status=JobStatus.PENDING
        )

        self.db.add(job)
        self.db.commit()        # persistir primero
        self.db.refresh(job)    # refresh para obtener ID generado

        # enviar a Redis (después del commit) ! Idealmente solo enviariamos el jobId
        try:
            self.queue.publish_reframe_job(
                job_id=str(job.id),
                video_id=str(video_id),
                user_id=str(user_id),
                start_sec=start_sec,
                end_sec=end_sec,
            )
        except Exception as e:
            # Si falla Redis, dejamos el job en FAILED
            job.status = JobStatus.FAILED
            job.error_message = "Error enviando job a la cola"
            self.db.commit()
            raise e

        return JobReframeResponse(
            job_id=job.id,
            job_type=job.job_type,
            status=job.status,
            filename=video.original_filename,
            start_sec=start_sec,
            end_sec=end_sec,
            created_at=job.created_at
        )