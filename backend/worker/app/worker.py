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
            text=True
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
    "ffmpeg": check_ffmpeg()
    }
    
    logger.info("🔎 Environment check:")
    for k, v in status.items():
        logger.info(f"{k}: {v}")



logger = setup_logging()
QUEUE_NAME = "reframe_queue"
def worker_loop():
    logger.info("🎧 Worker listening for jobs...\n")
        
    while True:
        payload = redis_client.pop_from_queue(QUEUE_NAME)

        if not payload:
            continue
        job_id = payload.get("job_id")
        start_sec = payload.get("start_sec")
        end_sec = payload.get("end_sec")
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
                logger.warning(f"❌Job {job_id} has invalid state {job.status}, skipping"
                )
                continue

            logger.info(f"⚙️  Processing job: {job_id} of type {job.job_type}")
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch job {job_id} from DB: {e}")
            db.close()

        try:
            filename = db.query(Video).filter(Video.id == job.video_id).first().original_filename
            if not filename:
                logger.warning(f"❌ Video {job.video_id} has no filename")
                job.status = JobStatus.FAILED
                db.commit()
                db.close()
                continue

            storage_path = db.query(Video).filter(Video.id == job.video_id).first().storage_path
            if not storage_path:
                logger.warning(f"❌ Video {job.video_id} has no storage_path")
                job.status = JobStatus.FAILED
                db.commit()
                db.close()
                continue

            job.status = JobStatus.RUNNING
            db.commit()
        except Exception as e:
            logger.error(f"❌ Failed to prepare job {job_id}: {e}") 

        
        if job.job_type == JobType.REFRAME:
            # ejecutar pipeline
            try:
                logger.info(f"⚙️  Processing REFRAME job {job.id}")
                video_url_response = video_worker_service.get_video_url(storage_path, expires_in=300)
                video_local_path = process(video_url_response, filename, start_sec, end_sec)
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed during pipeline execution: {e}")
                job.status = JobStatus.FAILED   
                job.error_message = str(e)
                db.commit()
                db.close()

            # upload to minio
            try:
                storage_path = video_worker_service.upload_local_video_to_minio(video_local_path, filename)
                logger.info(f"✅ Video uploaded to MinIO")
                public_storage_path = video_worker_service.get_video_public_url(storage_path, expires_in=300)
                logger.info(f"✅ Public MiniIO url: {public_storage_path}")
            except Exception as e:
                logger.error(f"❌ Job {job_id} failed during upload to MinIO: {e}")
                job.status = JobStatus.FAILED      
                job.error_message = str(e)
                db.commit()
                db.close()

           # update db
            try:
                job.output_path = public_storage_path
                job.status = JobStatus.DONE
                db.commit()
                # clear /tmp service...?
                logger.info(f"✅ Job {job_id} completed successfully")
                db.close()
            except Exception as e: 
                logger.error(f"❌ Job {job_id} failed during DB update: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()
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