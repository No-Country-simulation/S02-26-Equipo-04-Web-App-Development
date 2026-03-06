import redis
import json
import sys
import os
import subprocess
import logging
import cv2
import time
from pathlib import Path
import hashlib
from urllib.parse import urlparse
from urllib.request import urlretrieve
from app.pipeline import process
from app.pipeline import process_add_audio

# imports del nodo1 /api
from app.models.job import Job
from app.models.video import Video
from app.models.user import User
from app.models.enums import JobStatus, JobType
from app.services.storage_service import StorageService
from app.services.queue_service import QueueService
#from app.services.job_service import JobService
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

QUEUE_NAME = "reframe_queue"

queue_service = QueueService(redis_client)
storage_service = StorageService()

SOURCE_CACHE_DIR = Path(os.getenv("WORKER_SOURCE_CACHE_DIR", "/tmp/source_cache"))
SOURCE_CACHE_TTL_SECONDS = int(os.getenv("WORKER_SOURCE_CACHE_TTL_SECONDS", "1800"))


######################## ENVIRONMENT CHECKS #########################


LOG_LEVEL = logging.INFO  # o configurable desde env

def setup_worker_logger(name: str = None) -> logging.Logger:
    """
    Inicializa el logger del worker.
    - name: si se pasa, devuelve un logger con ese nombre; si no, devuelve root logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Evitar duplicar handlers si ya hay
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Evitar duplicados: los logs de este logger no se propagan al root
    logger.propagate = False

    return logger


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


def _resolve_source_video_path(source_storage_path: str) -> str:
    _ensure_source_cache_dir()
    _prune_source_cache(SOURCE_CACHE_TTL_SECONDS)

    cached_path = _cache_path_for_storage(source_storage_path)
    if cached_path.exists() and cached_path.stat().st_size > 0:
        age = time.time() - cached_path.stat().st_mtime
        if age <= SOURCE_CACHE_TTL_SECONDS:
            logger.info(f"📦 Reusing cached source video: {cached_path}")
            return str(cached_path)

    # Si ya es URL HTTP, la usamos tal cual
    parsed = urlparse(source_storage_path)
    if parsed.scheme in ("http", "https"):
        source_url = source_storage_path
    else:
        # Es un path S3 → generar presigned URL
        source_url = storage_service.get_video_url(source_storage_path, expires_in=300)
    logger.info(f"⬇️ Downloading source video to cache: {cached_path}")
    urlretrieve(source_url, cached_path)
    return str(cached_path)


######################## ENVIRONMENT CHECKS #########################
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



######################## WORKER METHODS #########################


def _get_video_from_job(job, job_service, storage_service):
    try:
        video = job.video
        if not video:
            job_service.update_status(job.id, JobStatus.FAILED, "No video")
            return None

        filename = video.original_filename
        if not filename:
            logger.error(f"❌ Video {job.video_id} has no filename")
            job_service.update_status(job.id, JobStatus.FAILED, "No filename")
            return None
        
        video_storage_path = video.storage_path
        
        return video, filename, video_storage_path

    except Exception as e:
        logger.error(f"❌ Failed to prepare job {job.id}: {e}")
        job_service.update_status(
            job.id,
            JobStatus.FAILED,
            error_message=str(e),
        )
        return


def handle_job(payload, job_service, queue_service, storage_service):
    job_id = payload.get("job_id")
    logger.info(f"🎬 Job received from Redis, Job id: {job_id}")

    job = job_service.get_by_id(job_id)

    if not job:
        logger.warning(f"Job {job_id} not found")
        return

    if job.status not in [JobStatus.PENDING, JobStatus.FAILED]:
        #logger.warning(f"Invalid job state {job.status}")
        return

    job_service.update_status(job.id, JobStatus.RUNNING)

    if job.job_type == JobType.AUTO_REFRAME:
        handle_auto_reframe(job, payload, job_service, storage_service)
        return
    
    if job.job_type == JobType.REFRAME:
        handle_reframe(job, payload, job_service, storage_service)
        return
    
    if job.job_type == JobType.ADD_AUDIO:
        handle_add_audio(job, payload, job_service, storage_service)
        return

    if job.job_type == JobType.CANCEL:
        handle_cancel(job, job_service)
        return

    job_service.update_status(job.id, JobStatus.FAILED, "Unknown job type")


def handle_cancel(job, job_service):
    logger.info(f"⚙️  Processing CANCEL job {job.id}")
    # TODO cancel(job.video_id)


def handle_add_audio_pipeline(job, payload, filename, video_url):

    logger.info(f"⚙️  Processing ADD_AUDIO job {job.id}")

    audio_storage_path = payload["audio_storage_path"]
    audio_offset_sec = payload["audio_offset_sec"]
    audio_start_sec = payload["audio_start_sec"]
    audio_end_sec = payload["audio_end_sec"]
    audio_volume = payload["audio_volume"]

    audio_url = storage_service.get_video_url(audio_storage_path)

    video_local_path = process_add_audio(
    video_url,
    filename,
    audio_url,
    audio_offset_sec,
    audio_start_sec,
    audio_end_sec,
    audio_volume
    )
    return video_local_path
        

def handle_reframe_pipeline(job, payload, filename, video_url):
    # ejecutar pipeline
    try:

        logger.info(f"⚙️  Processing REFRAME job {job.id}")

        start_sec = payload.get("start_sec")
        end_sec = payload.get("end_sec")
        output_style = payload.get("output_style", "vertical")
        content_profile = payload.get("content_profile", "interview")
        watermark = payload.get("watermark")
        subtitles = payload.get("subtitles")

        video_local_path, srt_local_path = process(
            video_url,
            filename,
            start_sec,
            end_sec,
            watermark,
            subtitles,
            output_style=output_style,
            content_profile=content_profile,
        )
        return video_local_path, srt_local_path
    
    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during pipeline execution: {e}")
        raise


def handle_add_audio(job, payload, job_service, storage_service):
    logger.info(f"⚙️  Processing ADD_AUDIO job {job.id}")

    result = _get_video_from_job(job, job_service, storage_service)
    if not result:
        return
    video, filename, video_storage_path = result
    
    try:
        video_cached_path = _resolve_source_video_path(video_storage_path)
        video_local_path = handle_add_audio_pipeline(job, payload, filename, video_cached_path)
    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during pipeline execution: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    try:
        output_filename = f"{job.id}.mp4"
        storage_path, bucket, key = storage_service.upload_local_video_to_minio(video_local_path, output_filename)
        logger.info(f"✅ Video uploaded to MinIO")
        
        public_storage_path = storage_service.get_video_public_url(
                storage_path, expires_in=300
            )
        logger.info(f"✅ Public MiniIO url: {public_storage_path}")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during upload to MinIO: {e}")
        job_service.update_status(
            job.id,
            JobStatus.FAILED,
            error_message=str(e),
        )
        return
    
    # update db
    try:
        job_service.update_status(
            job.id,
            status=JobStatus.DONE,
            error_message=None,
            video_path=storage_path
        )
        # clear /tmp service...?
        logger.info(f"✅ Job {job.id} completed successfully")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during DB update: {e}")
        job_service.update_status(
            job.id,
            status=JobStatus.FAILED,
            error_message=str(e),
        )

#ideo_url = storage_service.get_video_url(video.storage_path)
#       if not video_url:
#           logger.warning(f"❌ Video {job.video_id} has no storage_path")
#           job_service.update_status(job.id, JobStatus.FAILED, "No video URL")
#           return None

def handle_auto_reframe(job, payload, job_service, storage_service):
    logger.info(f"⚙️  Processing AUTO-REFRAME job {job.id}")

    result = _get_video_from_job(job, job_service, storage_service)
    if not result:
        # ya se actualizó el estado dentro de _get_video_from_job...
        return
    video, filename, video_storage_path = result

    try:
        # llamar calculos para auto frame
        clips_count = payload.get("clips_count")
        clip_duration_sec = payload.get("clip_duration_sec")
        requested_profile = payload.get("content_profile", "auto")
        watermark = payload.get("watermark")
        segments = job_service._build_auto_clip_ranges(video, clips_count, clip_duration_sec, requested_profile)
        logger.info(f"✅ Auto-reframe calculations completed. Segments: {segments}")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during auto-reframe calculations: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    # Crear jobs hijos REFRAME y publicarlos en Redis
    output_path_jobs=[]
    try:
        ranges, duration, resolved_profile = segments
        for start_sec, end_sec in ranges:
            new_job = job_service.create_reframe_job_for_worker(
                user_id=job.user_id,
                video_id=video.id,
                start_sec=start_sec,
                end_sec=end_sec,
                watermark=watermark,
                subtitles=True,
                output_style=payload.get("output_style", "vertical"),
                content_profile=resolved_profile,
                job_type=JobType.REFRAME
            )
            queue_service.publish_reframe_job(
                job_id=str(new_job.id),
                video_id=str(video.id),
                user_id=str(job.user_id),
                start_sec=start_sec,
                end_sec=end_sec,
                watermark=watermark,
                subtitles=True,
                output_style=payload.get("output_style", "vertical"),
                content_profile=resolved_profile,
            )
            output_path_jobs.append(str(new_job.id))

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during job creation: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    # Marcar job padre como COMPLETADO (esta completado al enviar nuevos jobs hijos)
    try:
        job_service.update_status(
            job_id=job.id,
            status=JobStatus.DONE,
            child_jobs=output_path_jobs
        )
        logger.info(f"✅ AUTO-REFRAME job {job.id} completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to update parent job {job.id} status: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))


def handle_reframe(job, payload, job_service, storage_service):
    
    result = _get_video_from_job(job, job_service, storage_service)
    if not result:
        # ya se actualizó el estado dentro de _get_video_from_job...
        return
    video, filename, video_storage_path = result

    try:
        video_cached_path = _resolve_source_video_path(video_storage_path)
        video_local_path, srt_local_path = handle_reframe_pipeline(job, payload, filename, video_cached_path)
    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during pipeline execution: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    try:
        output_filename = f"{job.id}.mp4"
        storage_path, bucket, key = storage_service.upload_local_video_to_minio(video_local_path, output_filename)
        logger.info(f"✅ Video uploaded to MinIO")
        
        public_storage_path = storage_service.get_video_public_url(
                storage_path, expires_in=300
            )
        logger.info(f"✅ Public MiniIO url: {public_storage_path}")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during upload to MinIO: {e}")
        job_service.update_status(
            job.id,
            JobStatus.FAILED,
            error_message=str(e),
        )
        return
    
    srt_storage_path = None
    if srt_local_path is not None:
        try:
            output_srt_filename = f"{job.id}.srt"
            srt_storage_path, bucket, key = storage_service.upload_local_video_to_minio(srt_local_path, output_srt_filename)
            logger.info(f"✅ Subtitles uploaded to MinIO")

            public_srt_storage_path = storage_service.get_video_public_url(
                    srt_storage_path, expires_in=300
                )
            logger.info(f"✅ Public Subtitles MiniIO url: {public_srt_storage_path}")

        except Exception as e:
            logger.error(f"❌ Job {job.id} failed during upload Subtitles to MinIO: {e}")
            job_service.update_status(
                job.id,
                JobStatus.FAILED,
                error_message=str(e),
            )
            return

    # update db
    try:
        # Guardamos storage path corto; la API regenera URL firmada al consultar.
        job_service.update_status(
            job.id,
            status=JobStatus.DONE,
            error_message=None,
            video_path=storage_path,
            subtitles_path=srt_storage_path
        )
        # clear /tmp service...?
        logger.info(f"✅ Job {job.id} completed successfully")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during DB update: {e}")
        job_service.update_status(
            job.id,
            status=JobStatus.FAILED,
            error_message=str(e),
        )


def worker_loop():
    logger.info("🎧 Worker listening for jobs...\n")

    while True:
        payload = redis_client.pop_from_queue(QUEUE_NAME)

        if not payload:
            continue

        db = SessionLocal()

        try:
            #job_service = JobService(db) Falta desacoplarlo de pydantic y los esquemas para poder usarlo!
            job_service = VideoWorkerService(db, storage_service, queue_service)

            handle_job(
                payload=payload,
                job_service=job_service,
                queue_service=queue_service,
                storage_service=storage_service
            )

        finally:
            db.close()


if __name__ == "__main__":
    logger = setup_worker_logger("worker")
    logger.info("=" * 50)
    logger.info(f"🎬 VIDEO WORKER")
    logger.info("=" * 50)

    check_dependencies()
    worker_loop()
