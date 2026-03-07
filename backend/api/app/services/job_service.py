from uuid import UUID
from typing import Any, Literal, Optional
from sqlalchemy import String, cast
from sqlalchemy.orm import Session
from urllib.parse import unquote, urlparse
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video
from app.models.audio import Audio

from app.schemas.job import (
    JobReframeResponse,
    JobStatusResponse,
    JobAutoReframeResponse2,
    UserClipDetailResponse,
    UserClipsResponse,
    UserClipItem,
    JobAddAudioResponse,
)

from app.services.queue_service import QueueService
from app.services.storage_service import StorageService
from app.core.logging import setup_logging
from app.utils.exceptions import (
    JobParameterException,
    NotFoundException,
    VideoDBException,
)

logger = setup_logging()

MIN_VIDEO_DURATION_SECS = 5


class JobService:
    """Servicio de Jobs - Persiste un Job, luego envia mensaje a Redis"""

    def __init__(
        self, db: Session, queue: QueueService, storage_service: StorageService
    ):
        self.db = db
        self.queue = queue
        self.storage = storage_service

    def _extract_storage_path(self, output_path: str | None) -> str | None:
        if not output_path:
            return None

        if output_path.startswith("s3://"):
            return output_path

        parsed = urlparse(output_path)
        normalized_path = parsed.path.lstrip("/")

        if not normalized_path:
            return None

        return f"s3://{unquote(normalized_path)}"

    def _extract_storage_paths(
        self, output_path: dict[str, Any] | str | None
    ) -> list[str]:
        if not output_path:
            return []

        if isinstance(output_path, str):
            normalized = self._extract_storage_path(output_path)
            return [normalized] if normalized else []

        if not isinstance(output_path, dict):
            return []

        values = [output_path.get("video"), output_path.get("subtitles")]
        result: list[str] = []

        for value in values:
            if not isinstance(value, str):
                continue

            normalized = self._extract_storage_path(value)
            if normalized:
                result.append(normalized)

        return list(dict.fromkeys(result))

    def _resolve_output_urls(
        self, output_path: dict[str, str] | None
    ) -> dict[str, str] | None:
        """
        Convierte todas las rutas S3 de un output_path JSON a URLs públicas presignadas.
        output_path: dict con keys como "video", "subtitles", etc. y valores S3 paths.

        Devuelve un dict con las mismas keys y URLs públicas.
        """
        if not output_path:
            return None

        resolved: dict[str, str] = {}

        for key, value in output_path.items():
            if not value:
                resolved[key] = None
                continue

            # Si es lista (ej: jobs) la dejamos igual
            if isinstance(value, list):
                resolved[key] = value
                continue

            # Si es None
            if not value:
                resolved[key] = None
                continue

            # Si no es string, lo dejamos igual
            if not isinstance(value, str):
                resolved[key] = value
                continue

            storage_path = self._extract_storage_path(value)
            if not storage_path:
                # Si no es un path S3 válido, devolvemos el valor tal cual
                resolved[key] = value
                continue

            try:
                resolved[key] = self.storage.get_video_public_url(
                    storage_path, expires_in=3600
                )
            except Exception as exc:
                logger.warning(f"No se pudo generar URL pública para '{key}': {exc}")
                resolved[key] = value

        return resolved

    def get_job_status(self, job_id: UUID, user_id: UUID) -> JobStatusResponse:
        job = (
            self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        )

        if not job:
            raise NotFoundException("Job Not found")

        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            output_path=self._resolve_output_urls(job.output_path),
        )

    def _get_user_video(self, video_id: UUID, user_id: UUID) -> Video:
        video = (
            self.db.query(Video)
            .filter(Video.id == video_id, Video.user_id == user_id)
            .first()
        )

        if not video:
            raise NotFoundException("Video not found")

        return video

    def _get_user_audio(self, audio_id: UUID, user_id: UUID) -> Audio:
        audio = (
            self.db.query(Audio)
            .filter(Audio.id == audio_id, Audio.user_id == user_id)
            .first()
        )

        if not audio:
            raise NotFoundException("Audio not found")

        return audio

    def _validate_time_range(self, start_sec: int, end_sec: int) -> None:
        if (
            start_sec < 0
            or start_sec > end_sec
            or end_sec <= 0
            or (end_sec - start_sec) < MIN_VIDEO_DURATION_SECS
        ):
            raise JobParameterException()

    def _create_reframe_job(
        self,
        *,
        video: Video,
        user_id: UUID,
        start_sec: int,
        end_sec: int,
        allow_reuse: bool,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
        content_profile: Literal["auto", "interview", "sports", "music"] = "auto",
        job_type: JobType = JobType.REFRAME,
        watermark: str | None,
        subtitles: bool | None,
    ) -> JobReframeResponse:

        self._validate_time_range(start_sec, end_sec)

        if watermark is None:
            watermark = "Hacelo Corto"

        if subtitles is None:
            subtitles = False

        existing_job = None
        if allow_reuse:
            existing_job = (
                self.db.query(Job)
                .filter(
                    Job.video_id == video.id,
                    Job.status.in_(
                        [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED]
                    ),
                )
                .first()
            )

        if existing_job and existing_job.status == JobStatus.RUNNING:
            logger.info(
                f"Existing job {existing_job.id} found for video {video.id} with status {existing_job.status}"
            )
            return JobReframeResponse(
                job_id=existing_job.id,
                job_type=existing_job.job_type,
                status=existing_job.status,
                filename=video.original_filename,
                start_sec=start_sec,
                end_sec=end_sec,
                created_at=existing_job.created_at,
            )

        if existing_job:
            logger.info(
                f"Existing job {existing_job.id} found for video {video.id} with status {existing_job.status}, reusing it"
            )
            try:
                self.queue.publish_reframe_job(
                    job_id=str(existing_job.id),
                    video_id=str(video.id),
                    user_id=str(user_id),
                    start_sec=start_sec,
                    end_sec=end_sec,
                    output_style=output_style,
                    content_profile=content_profile,
                    watermark=watermark,
                    subtitles=subtitles,
                )
            except Exception as e:
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
                created_at=existing_job.created_at,
            )

        job = Job(
            user_id=user_id,
            video_id=video.id,
            job_type=job_type,
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        try:
            self.queue.publish_reframe_job(
                job_id=str(job.id),
                video_id=str(video.id),
                user_id=str(user_id),
                start_sec=start_sec,
                end_sec=end_sec,
                output_style=output_style,
                content_profile=content_profile,
                watermark=watermark,
                subtitles=subtitles,
            )
        except Exception as e:
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
            created_at=job.created_at,
        )

    def _create_auto_reframe_job(
        self,
        *,
        video: Video,
        user_id: UUID,
        clips_count: int | None,
        clip_duration_sec: int | None,
        allow_reuse: bool,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
        content_profile: Literal["auto", "interview", "sports", "music"] = "auto",
        job_type: JobType = JobType.AUTO_REFRAME,
        watermark: str | None,
        subtitles: bool | None,
    ) -> JobReframeResponse:

        if not clips_count or clips_count < 1:
            raise JobParameterException("clips_count must be at least 1")
        if clip_duration_sec is not None and clip_duration_sec < 5:
            raise JobParameterException("clip_duration_sec must be at least 5 seconds")
        if watermark is None:
            watermark = "Hacelo Corto"
        if subtitles is None:
            subtitles = False

        job = Job(
            user_id=user_id,
            video_id=video.id,
            job_type=job_type,
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        try:
            self.queue.publish_auto_reframe_job(
                job_id=str(job.id),
                video_id=str(video.id),
                user_id=str(user_id),
                clips_count=clips_count,
                clip_duration_sec=clip_duration_sec,
                output_style=output_style,
                content_profile=content_profile,
                watermark=watermark,
                subtitles=subtitles,
            )
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = "Error enviando job a la cola"
            self.db.commit()
            raise e

        return JobAutoReframeResponse2(
            job_id=job.id,
            job_type=job.job_type,
            status=job.status,
            filename=video.original_filename,
            total_jobs=clips_count or 0,
            created_at=job.created_at,
        )

    def reframe_video(
        self,
        video_id: UUID,
        user_id: UUID,
        job_type: JobType,
        start_sec: int,
        end_sec: int,
        crop_to_vertical: bool | None = None,
        subtitles: bool | None = None,
        face_tracking: bool | None = None,
        color_filter: bool | None = None,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
        content_profile: Literal["auto", "interview", "sports", "music"] = "auto",
        watermark: str | None = None,
    ) -> JobReframeResponse:

        video = self._get_user_video(video_id, user_id)

        self._validate_time_range(start_sec, end_sec)

        logger.info(f"Reframe for video: {video_id}, job_type: {job_type}")

        return self._create_reframe_job(
            video=video,
            user_id=user_id,
            start_sec=start_sec,
            end_sec=end_sec,
            allow_reuse=False,
            output_style=output_style,
            content_profile=content_profile,
            job_type=job_type,
            watermark=watermark,
            subtitles=subtitles,
        )

    def auto_reframe_video2(
        self,
        video_id: UUID,
        user_id: UUID,
        job_type: JobType.AUTO_REFRAME,
        clips_count: int | None,
        clip_duration_sec: int | None,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
        content_profile: Literal["auto", "interview", "sports", "music"] = "auto",
        watermark: str | None = None,
        subtitles: bool | None = None,
    ) -> JobReframeResponse:

        video = self._get_user_video(video_id, user_id)

        logger.info(
            f"AUTO_REFRAME for video: {video_id}, job_type: {JobType.AUTO_REFRAME}"
        )

        return self._create_auto_reframe_job(
            video=video,
            user_id=user_id,
            clips_count=clips_count,
            clip_duration_sec=clip_duration_sec,
            allow_reuse=False,
            output_style=output_style,
            content_profile=content_profile,
            job_type=JobType.AUTO_REFRAME,
            watermark=watermark,
            subtitles=subtitles,
        )

    def list_user_clips(
        self, user_id: UUID, limit: int = 20, offset: int = 0, query: str | None = None
    ) -> UserClipsResponse:
        base_query = (
            self.db.query(Job, Video)
            .join(Video, Video.id == Job.video_id)
            .filter(
                Job.user_id == user_id,
                Job.job_type.in_([JobType.REFRAME, JobType.ADD_AUDIO]),
                Job.output_path.isnot(None),
            )
        )

        cleaned_query = (query or "").strip()
        if cleaned_query:
            like_term = f"%{cleaned_query}%"
            base_query = base_query.filter(
                (Video.original_filename.ilike(like_term))
                | (cast(Job.id, String).ilike(like_term))
            )

        total = base_query.count()
        rows = (
            base_query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
        )

        clips = [
            UserClipItem(
                job_id=job.id,
                video_id=job.video_id,
                job_type=job.job_type,
                status=job.status,
                output_path=self._resolve_output_urls(job.output_path),
                source_filename=video.original_filename,
                created_at=job.created_at,
            )
            for job, video in rows
        ]

        return UserClipsResponse(total=total, limit=limit, offset=offset, clips=clips)

    def get_user_clip(self, job_id: UUID, user_id: UUID) -> UserClipDetailResponse:
        row = (
            self.db.query(Job, Video)
            .join(Video, Video.id == Job.video_id)
            .filter(
                Job.id == job_id,
                Job.user_id == user_id,
                Job.job_type.in_([JobType.REFRAME, JobType.ADD_AUDIO]),
            )
            .first()
        )

        if not row:
            raise NotFoundException("Clip no encontrado")

        job, video = row
        clip = UserClipItem(
            job_id=job.id,
            video_id=job.video_id,
            job_type=job.job_type,
            status=job.status,
            output_path=self._resolve_output_urls(job.output_path),
            source_filename=video.original_filename,
            created_at=job.created_at,
        )
        return UserClipDetailResponse(clip=clip)

    def delete_user_clip(self, job_id: UUID, user_id: UUID) -> None:
        job = (
            self.db.query(Job)
            .filter(
                Job.id == job_id,
                Job.user_id == user_id,
                Job.job_type.in_([JobType.REFRAME, JobType.ADD_AUDIO]),
            )
            .first()
        )

        if not job:
            raise NotFoundException("Clip no encontrado")

        if job.output_path:
            storage_paths = self._extract_storage_paths(job.output_path)
            for storage_path in storage_paths:
                self.storage.delete_video_from_storage(storage_path)

        try:
            self.db.delete(job)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error eliminando clip", str(exc))

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        error_message: str | None = None,
        video_path: Optional[str] = None,
        subtitles_path: Optional[str] = None,
    ) -> bool:
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.warning(f"❌ Job {job_id} not found in DB for status update")
                return False

            # Crear output_path como dict JSON solo con lo que exista
            output_path = {
                k: v
                for k, v in {"video": video_path, "subtitles": subtitles_path}.items()
                if v is not None
            }

            job.status = status
            job.error_message = error_message or None
            job.output_path = output_path or None

            self.db.commit()
            return True

        except Exception as exc:
            self.db.rollback()
            logger.error(f"❌ Could not persist state for job {job_id}: {exc}")
            return False

    def get_by_id(self, job_id: UUID) -> Job:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundException("Job not found")
        return job

    def add_audio_to_video(
        self,
        user_id: UUID,
        video_id: UUID,
        audio_id: UUID,
        audio_offset_sec: int,
        audio_start_sec: int,
        audio_end_sec: int,
        audio_volume: float,
    ) -> JobAddAudioResponse:

        self._validate_time_range(audio_start_sec, audio_end_sec)

        video = self._get_user_video(video_id, user_id)

        audio = self._get_user_audio(audio_id, user_id)

        existing_job = None
        existing_job = (
            self.db.query(Job)
            .filter(
                Job.video_id == video.id,
                Job.user_id == user_id,
                Job.status.in_(
                    [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED]
                ),
            )
            .first()
        )

        if existing_job and existing_job.status == JobStatus.RUNNING:
            logger.info(
                f"Existing job {existing_job.id} found for video {video.id} with status {existing_job.status}"
            )
            return JobAddAudioResponse(
                job_id=existing_job.id,
                job_type=existing_job.job_type,
                status=existing_job.status,
                filename=video.original_filename,
                audio_filename=audio.original_filename,
                audio_volume=audio_volume,
                created_at=existing_job.created_at,
            )

        if existing_job:
            logger.info(
                f"Existing job {existing_job.id} found for video {video.id} with status {existing_job.status}, reusing it"
            )
            try:
                self.queue.publish_add_audio_job(
                    job_id=str(existing_job.id),
                    job_type=str(existing_job.job_type),
                    video_id=str(video.id),
                    user_id=str(user_id),
                    audio_storage_path=audio.storage_path,
                    audio_offset_sec=audio_offset_sec,
                    audio_start_sec=audio_start_sec,
                    audio_end_sec=audio_end_sec,
                    audio_volume=audio_volume,
                )
            except Exception as e:
                existing_job.status = JobStatus.FAILED
                existing_job.error_message = "Error enviando job a la cola"
                self.db.commit()
                raise e

            return JobAddAudioResponse(
                job_id=existing_job.id,
                job_type=existing_job.job_type,
                status=existing_job.status,
                filename=video.original_filename,
                audio_filename=audio.original_filename,
                audio_volume=audio_volume,
                created_at=existing_job.created_at,
            )

        job = Job(
            user_id=user_id,
            video_id=video.id,
            job_type=JobType.ADD_AUDIO,
            status=JobStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        try:
            self.queue.publish_add_audio_job(
                job_id=str(job.id),
                job_type=str(job.job_type),
                video_id=str(video.id),
                user_id=str(user_id),
                audio_storage_path=audio.storage_path,
                audio_offset_sec=audio_offset_sec,
                audio_start_sec=audio_start_sec,
                audio_end_sec=audio_end_sec,
                audio_volume=audio_volume,
            )
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = "Error enviando job a la cola"
            self.db.commit()
            raise e

        return JobAddAudioResponse(
            job_id=job.id,
            job_type=job.job_type,
            status=job.status,
            filename=video.original_filename,
            audio_filename=audio.original_filename,
            audio_volume=audio_volume,
            created_at=job.created_at,
        )
