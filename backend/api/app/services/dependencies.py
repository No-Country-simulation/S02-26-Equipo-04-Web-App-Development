from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.utils.redis_client import redis_client
from app.services.job_service import JobService
from app.services.storage_service import StorageService
from app.services.queue_service import QueueService
from app.services.video_service import VideoService
from app.services.audio_service import AudioService


def get_storage_service() -> StorageService:
    return StorageService()

def get_queue_service() -> QueueService:
    return QueueService(redis_client)


def get_video_service(
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> VideoService:
    return VideoService(db, storage)

def get_audio_service(
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
) -> AudioService:
    return AudioService(db, storage)

def get_job_service(
    db: Session = Depends(get_db),
    queue: QueueService = Depends(get_queue_service),
    storage: StorageService = Depends(get_storage_service),
) -> JobService:
    return JobService(db, queue, storage)

