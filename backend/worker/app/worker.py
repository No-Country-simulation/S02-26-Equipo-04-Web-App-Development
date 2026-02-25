import redis
import json
import os
import subprocess
import cv2
import time
from worker.app.pipeline import process

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


logger = setup_logging()
QUEUE_NAME = "reframe_queue"

queue_service = QueueService(redis_client)
storage_service = StorageService()

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

def handle_job(payload, job_service, queue_service, storage_service):
    job_id = payload.get("job_id")
    logger.info(f"🎬 Job received from Redis, Job id: {job_id}")

    job = job_service.get_by_id(job_id)

    if not job:
        logger.warning(f"Job {job_id} not found")
        return

    if job.status not in [JobStatus.PENDING, JobStatus.FAILED]:
        logger.warning(f"Invalid job state {job.status}")
        return

    job_service.update_status(job.id, JobStatus.RUNNING)

    if job.job_type == JobType.AUTO_REFRAME:
        handle_auto_reframe(job, payload, job_service, storage_service)
        return
    
    if job.job_type == JobType.REFRAME:
        handle_reframe(job, payload, job_service, storage_service)
        return

    if job.job_type == JobType.CANCEL:
        handle_cancel(job, job_service)
        return

    job_service.update_status(job.id, JobStatus.FAILED, "Unknown job type")


def handle_cancel(job, job_service):
    logger.info(f"⚙️  Processing CANCEL job {job.id}")
    # TODO cancel(job.video_id)


def handle_reframe_pipeline(job, payload, filename, video_url):
    # ejecutar pipeline
    try:
        # recuperar datos del payload
        start_sec = payload.get("start_sec")
        end_sec = payload.get("end_sec")
        output_style = payload.get("output_style", "vertical")
        content_profile = payload.get("content_profile", "interview")
        logger.info(f"⚙️  Processing REFRAME job {job.id}")

        video_local_path = process(
            video_url,
            filename,
            start_sec,
            end_sec,
            output_style=output_style,
            content_profile=content_profile,
        )
        return video_local_path
    
    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during pipeline execution: {e}")
        raise


def _get_video_from_job(job, job_service, storage_service):
    try:
        video = job.video
        if not video:
            job_service.update_status(job.id, JobStatus.FAILED, "No video")
            return None

        filename = video.original_filename
        if not filename:
            logger.warning(f"❌ Video {job.video_id} has no filename")
            job_service.update_status(job.id, JobStatus.FAILED, "No filename")
            return None
        
        video_url = storage_service.get_video_url(video.storage_path)
        if not video_url:
            logger.warning(f"❌ Video {job.video_id} has no storage_path")
            job_service.update_status(job.id, JobStatus.FAILED, "No video URL")
            return None
        
        return video, filename, video_url

    except Exception as e:
        logger.error(f"❌ Failed to prepare job {job.id}: {e}")
        job_service.update_status(
            job.id,
            JobStatus.FAILED,
            error_message=str(e),
        )
        return


def handle_auto_reframe(job, payload, job_service, storage_service):
    logger.info(f"⚙️  Processing AUTO-REFRAME job {job.id}")

    result = _get_video_from_job(job, job_service, storage_service)
    if not result:
        # ya se actualizó el estado dentro de _get_video_from_job...
        return
    video, filename, video_url = result

    try:
        # llamar calculos para auto frame
        clips_count = payload.get("clips_count")
        clip_duration_sec = payload.get("clip_duration_sec")
        requested_profile = payload.get("content_profile", "auto")
        segments = job_service._build_auto_clip_ranges(video, clips_count, clip_duration_sec, requested_profile)
        logger.info(f"✅ Auto-reframe calculations completed. Segments: {segments}")

    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during auto-reframe calculations: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    # Crear jobs hijos REFRAME y publicarlos en Redis
    try:
        ranges, duration, resolved_profile = segments
        for start_sec, end_sec in ranges:
            new_job = job_service.create_reframe_job_for_worker(
                user_id=job.user_id,
                video_id=video.id,
                start_sec=start_sec,
                end_sec=end_sec,
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
                output_style=payload.get("output_style", "vertical"),
                content_profile=resolved_profile,
            )
    except Exception as e:
        logger.error(f"❌ Job {job.id} failed during job creation: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))
        return
    
    # Marcar job padre como COMPLETADO (esta completado al enviar nuevos jobs hijos)
    try:
        job_service.update_status(job.id, JobStatus.DONE)
        logger.info(f"✅ AUTO-REFRAME job {job.id} completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to update parent job {job.id} status: {e}")
        job_service.update_status(job.id, JobStatus.FAILED, str(e))


def handle_reframe(job, payload, job_service, storage_service):
    
    result = _get_video_from_job(job, job_service, storage_service)
    if not result:
        # ya se actualizó el estado dentro de _get_video_from_job...
        return
    video, filename, video_url = result

    try:
        video_local_path = handle_reframe_pipeline(job, payload, filename, video_url)
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
        # Guardamos storage path corto; la API regenera URL firmada al consultar.
        job_service.update_status(
            job.id,
            status=JobStatus.DONE,
            error_message=None,
            output_path=storage_path
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
    logger.info("=" * 50)
    logger.info(f"🎬 VIDEO WORKER")
    logger.info("=" * 50)

    check_dependencies()
    worker_loop()
