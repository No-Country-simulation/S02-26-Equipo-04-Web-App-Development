import json
from app.core.logging import setup_logging
from app.models.enums import JobType

logger = setup_logging()


class QueueService:
    def __init__(self, redis_client):
        self.redis = redis_client

    def publish_add_audio_job(
        self,
        job_id: str,
        job_type: str,
        video_id: str,
        user_id: str,
        audio_storage_path: str,
        audio_offset_sec: int,
        audio_start_sec: int,
        audio_end_sec: int,
        audio_volume: str,
        source_video_storage_path: str | None = None,
        source_video_filename: str | None = None,
    ):
        payload = {
            "job_id": job_id,
            "job_type": job_type,
            "video_id": video_id,
            "user_id": user_id,
            "audio_storage_path": audio_storage_path,
            "audio_offset_sec": audio_offset_sec,
            "audio_start_sec": audio_start_sec,
            "audio_end_sec": audio_end_sec,
            "audio_volume": audio_volume,
            "source_video_storage_path": source_video_storage_path,
            "source_video_filename": source_video_filename,
        }

        self.redis.push_to_queue("reframe_queue", payload)

        logger.info(f"👷 Job: {job_id} sent to Worker via Redis")

    def publish_reframe_job(
        self,
        job_id: str,
        video_id: str,
        user_id: str,
        start_sec: int,
        end_sec: int,
        watermark: str,
        subtitles: bool,
        output_style: str = "vertical",
        content_profile: str = "interview",
    ):
        # idealmente, solo enviamos job_id y que el worker consulte tabla Jobs;
        payload = {
            "job_id": job_id,
            "video_id": video_id,
            "user_id": user_id,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "output_style": output_style,
            "content_profile": content_profile,
            "type": JobType.REFRAME.value,
            "watermark": watermark,
            "subtitles": subtitles,
        }
        self.redis.push_to_queue("reframe_queue", payload)

        logger.info(f"👷 Job: {job_id} sent to Worker via Redis")

    def publish_auto_reframe_job(
        self,
        job_id: str,
        video_id: str,
        user_id: str,
        clips_count: int,
        clip_duration_sec: int,
        watermark: str,
        subtitles: bool = False,
        output_style: str = "vertical",
        content_profile: str = "interview",
    ):
        payload = {
            "job_id": job_id,
            "video_id": video_id,
            "user_id": user_id,
            "clips_count": clips_count,
            "clip_duration_sec": clip_duration_sec,
            "output_style": output_style,
            "content_profile": content_profile,
            "type": JobType.AUTO_REFRAME.value,
            "watermark": watermark,
            "subtitles": subtitles,
        }

        self.redis.push_to_queue("reframe_queue", payload)

        logger.info(f"👷 Job: {job_id} sent to Worker via Redis")
