import redis
import json
import os
import subprocess
import cv2
import time
import hashlib
from pathlib import Path
from urllib.request import urlretrieve
from worker.app.pipeline import process

# imports del nodo1 /api
from app.models.job import Job
from app.models.video import Video
from app.models.user import User
from app.models.enums import JobStatus, JobType
from app.services.video_worker_service import VideoWorkerService
from app.database.base import SessionLocal
from app.utils.redis_client import redis_client
from app.core.logging import setup_logging

"""
============================
    worker.py
============================

worker.py
 ├── init redis                     -> escucha peticiones de la API
 ├── init db session                -> para actualizar estado del Job
 ├── loop                           -> llama a pipeline.py
 │     ├── esperar job (BRPOP)
 │     ├── set status RUNNING       -> escribe en Db tabla Jobs
 │     ├── ejecutar pipeline
 │     ├── set status COMPLETED     -> escribe en Db tabla Jobs
 │     └── manejar FAILED           -> escribe en Db tabla Jobs

"""


def check_ffmpeg():
    """
    Verifica que FFmpeg esté instalado en el contenedor
    y accesible desde el PATH del sistema.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.split("\n")[0]
    except Exception as e:
        return f"FFmpeg error: {e}"


def check_opencv():
    """
    Verifica que OpenCV esté correctamente instalado
    e importable desde Python.
    """
    try:
        return f"OpenCV version {cv2.__version__}"
    except Exception as e:
        return f"OpenCV error: {e}"


def check_redis():
    """
    Verifica conexión con Redis usando la variable de entorno REDIS_HOST.
    """
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
        r.ping()
        return "Redis connected"
    except Exception as e:
        return f"Redis error: {e}"


def check_dependencies():
    """
    Ejecuta todos los chequeos de entorno al iniciar el worker.
    Sirve para validar que el contenedor está correctamente armado.
    """
    status = {
        "redis": check_redis(),
        "opencv": check_opencv(),
        "ffmpeg": check_ffmpeg(),
    }

    logger.info("🔎 Environment check:")
    for k, v in status.items():
        logger.info(f"{k}: {v}")


logger = setup_logging()
QUEUE_NAME = "reframe_queue"
SOURCE_CACHE_DIR = Path(os.getenv("WORKER_SOURCE_CACHE_DIR", "tmp/source_cache"))
SOURCE_CACHE_TTL_SECONDS = int(os.getenv("WORKER_SOURCE_CACHE_TTL_SECONDS", "1800"))


def _ensure_source_cache_dir() -> None:
    SOURCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path_for_storage(storage_path: str) -> Path:
    key = hashlib.sha1(storage_path.encode("utf-8")).hexdigest()
    return SOURCE_CACHE_DIR / f"{key}.mp4"


def _prune_source_cache(max_age_seconds: int) -> None:
    now = time.time()
    for path in SOURCE_CACHE_DIR.glob("*.mp4"):
        try:
            age = now - path.stat().st_mtime
            if age > max_age_seconds:
                path.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning(f"⚠️ Could not prune cache file {path}: {exc}")


def _resolve_source_video_path(
    video_worker_service: VideoWorkerService, source_storage_path: str
) -> str:
    _ensure_source_cache_dir()
    _prune_source_cache(SOURCE_CACHE_TTL_SECONDS)

    cached_path = _cache_path_for_storage(source_storage_path)
    if cached_path.exists() and cached_path.stat().st_size > 0:
        age = time.time() - cached_path.stat().st_mtime
        if age <= SOURCE_CACHE_TTL_SECONDS:
            logger.info(f"📦 Reusing cached source video: {cached_path}")
            return str(cached_path)

    source_url = video_worker_service.get_video_url(source_storage_path, expires_in=300)
    logger.info(f"⬇️ Downloading source video to cache: {cached_path}")
    urlretrieve(source_url, cached_path)
    return str(cached_path)


def update_job_state(db, job_id, **fields):
    try:
        updated_rows = (
            db.query(Job)
            .filter(Job.id == job_id)
            .update(fields, synchronize_session=False)
        )
        db.commit()
        if updated_rows == 0:
            logger.warning(f"⚠️ Job {job_id} no longer exists while updating state")
            return False
        return True
    except Exception as exc:
        db.rollback()
        logger.error(f"❌ Could not persist state for job {job_id}: {exc}")
        return False


def worker_loop():
    logger.info("🎧 Worker listening for jobs...\n")

    while True:
        payload = redis_client.pop_from_queue(QUEUE_NAME)

        if not payload:
            continue
        job_id = payload.get("job_id")
        start_sec = payload.get("start_sec")
        end_sec = payload.get("end_sec")
        output_style = payload.get("output_style", "vertical")
        content_profile = payload.get("content_profile", "interview")
        logger.info(f"🎬 Job received from Redis, Job id: {job_id}")

        db = SessionLocal()
        video_worker_service = VideoWorkerService()

        try:
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                db.close()
                logger.warning(f"❌ Job {job_id} not found in DB")
                continue

            if job.status != JobStatus.PENDING and job.status != JobStatus.FAILED:
                db.close()
                logger.warning(
                    f"❌Job {job_id} has invalid state {job.status}, skipping"
                )
                continue

            logger.info(f"⚙️  Processing job: {job_id} of type {job.job_type}")

        except Exception as e:
            logger.error(f"❌ Failed to fetch job {job_id} from DB: {e}")
            db.close()
            continue

        try:
            filename = (
                db.query(Video)
                .filter(Video.id == job.video_id)
                .first()
                .original_filename
            )
            if not filename:
                logger.warning(f"❌ Video {job.video_id} has no filename")
                update_job_state(
                    db,
                    job.id,
                    status=JobStatus.FAILED,
                    error_message="Video sin filename",
                )
                db.close()
                continue

            source_storage_path = (
                db.query(Video).filter(Video.id == job.video_id).first().storage_path
            )
            if not source_storage_path:
                logger.warning(f"❌ Video {job.video_id} has no storage_path")
                update_job_state(
                    db,
                    job.id,
                    status=JobStatus.FAILED,
                    error_message="Video sin storage_path",
                )
                db.close()
                continue

            if not update_job_state(db, job.id, status=JobStatus.RUNNING):
                db.close()
                continue
        except Exception as e:
            logger.error(f"❌ Failed to prepare job {job_id}: {e}")
            db.close()
            continue

        if job.job_type == JobType.REFRAME:
            # ejecutar pipeline
            try:
                logger.info(f"⚙️  Processing REFRAME job {job.id}")
                source_video_path = _resolve_source_video_path(
                    video_worker_service,
                    source_storage_path,
                )
                video_local_path = process(
                    source_video_path,
                    filename,
                    start_sec,
                    end_sec,
                    output_style=output_style,
                    content_profile=content_profile,
                )
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed during pipeline execution: {e}")
                update_job_state(
                    db,
                    job.id,
                    status=JobStatus.FAILED,
                    error_message=str(e),
                )
                db.close()
                continue

            # upload to minio
            try:
                output_filename = f"{job.id}.mp4"
                storage_path = video_worker_service.upload_local_video_to_minio(
                    video_local_path, output_filename
                )
                logger.info(f"✅ Video uploaded to MinIO")
                public_storage_path = video_worker_service.get_video_public_url(
                    storage_path, expires_in=300
                )
                logger.info(f"✅ Public MiniIO url: {public_storage_path}")
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed during upload to MinIO: {e}")
                update_job_state(
                    db,
                    job.id,
                    status=JobStatus.FAILED,
                    error_message=str(e),
                )
                db.close()
                continue

            # update db
            try:
                # Guardamos storage path corto; la API regenera URL firmada al consultar.
                persisted = update_job_state(
                    db,
                    job.id,
                    output_path=storage_path,
                    status=JobStatus.DONE,
                    error_message=None,
                )
                # clear /tmp service...?
                if persisted:
                    logger.info(f"✅ Job {job_id} completed successfully")
                db.close()
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed during DB update: {e}")
                update_job_state(
                    db,
                    job.id,
                    status=JobStatus.FAILED,
                    error_message=str(e),
                )
                db.close()

        elif job.job_type == JobType.CANCEL:
            logger.info(f"⚙️  Processing CANCEL job {job.id}")
            # TODO cancel(job.video_id)

        else:
            logger.warning(f"❌ Unknown job type {job.job_type} for job {job.id}")
            continue


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info(f"🎬 VIDEO WORKER")
    logger.info("=" * 50)

    check_dependencies()
    worker_loop()
