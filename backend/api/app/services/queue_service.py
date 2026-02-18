import json
from app.core.logging import setup_logging

logger = setup_logging()

class QueueService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def publish_reframe_job(self, job_id: str, video_id: str, user_id: str):
        # idealmente, solo enviamos job_id y que el worker consulte tabla Jobs; 
        payload = {
            "job_id": job_id,
            "video_id": video_id,
            "user_id": user_id,
            "type": "REFRAME"
        }
        self.redis.push_to_queue("reframe_queue", payload)

        logger.info(f"\n👷🏻‍♂️ Job: {job_id} sent to Worker via Redis\n")
