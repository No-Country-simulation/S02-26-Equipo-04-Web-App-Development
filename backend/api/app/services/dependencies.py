from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.utils.redis_client import redis_client
from app.services.job_service import JobService
from app.services.queue_service import QueueService


def get_queue_service() -> QueueService:
    return QueueService(redis_client)


def get_job_service(
    db: Session = Depends(get_db),
    queue: QueueService = Depends(get_queue_service),
) -> JobService:
    return JobService(db, queue)