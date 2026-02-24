from uuid import UUID
import re
import subprocess
from typing import Literal
from urllib.parse import unquote, urlparse
from sqlalchemy import String, cast
from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video
from app.schemas.job import (
    JobReframeResponse,
    JobStatusResponse,
    JobAutoReframeResponse,
    JobAutoReframeItem,
    UserClipDetailResponse,
    UserClipsResponse,
    UserClipItem,
)
from app.services.queue_service import QueueService
from app.services.video_worker_service import VideoWorkerService
from app.core.logging import setup_logging
from app.utils.exceptions import (
    JobParameterException,
    NotFoundException,
    VideoDBException,
)

logger = setup_logging()


class JobService:
    """Servicio de Jobs - Persiste un Job, luego envia mensaje a Redis"""

    def __init__(self, db: Session, queue: QueueService):
        self.db = db
        self.queue = queue

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

    def _resolve_output_url(self, output_path: str | None) -> str | None:
        if not output_path:
            return None

        storage_path = self._extract_storage_path(output_path)
        if not storage_path:
            return output_path

        try:
            return VideoWorkerService().get_video_public_url(
                storage_path, expires_in=3600
            )
        except Exception as exc:
            logger.warning(f"No se pudo regenerar URL de salida para clip: {exc}")
            return output_path

    def get_job_status(self, job_id: UUID, user_id: UUID) -> JobStatusResponse:
        job = (
            self.db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        )

        if not job:
            raise NotFoundException("Job Not found")

        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            output_path=self._resolve_output_url(job.output_path),
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

    def _validate_time_range(self, start_sec: int, end_sec: int) -> None:
        if start_sec < 0 or start_sec > end_sec:
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
    ) -> JobReframeResponse:
        self._validate_time_range(start_sec, end_sec)

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
                f"Existing job {existing_job.id} is already {existing_job.status}"
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
            job_type=JobType.REFRAME,
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

    def _build_auto_clip_ranges(
        self, video: Video, clips_count: int, clip_duration_sec: int
    ) -> tuple[list[tuple[int, int]], int | None]:
        duration = self._resolve_video_duration(video)

        if not duration or duration <= 0:
            starts = [i * clip_duration_sec for i in range(clips_count)]
            return ([(start, start + clip_duration_sec) for start in starts], None)

        safe_clip_duration = min(clip_duration_sec, max(5, duration))
        max_start = max(duration - safe_clip_duration, 0)
        source_url = self._get_source_url(video)

        if not source_url:
            starts = self._distributed_starts(max_start, clips_count)
            ranges = [
                (start, min(start + safe_clip_duration, duration)) for start in starts
            ]
            return (ranges, duration)

        highlights = self._extract_nonsilent_segments(source_url, duration)
        starts: list[int] = []
        min_gap = max(1, safe_clip_duration // 2)

        if highlights:
            scored = sorted(highlights, key=lambda seg: seg[1] - seg[0], reverse=True)
            for start_h, end_h in scored:
                center = (start_h + end_h) / 2
                start = int(round(center - (safe_clip_duration / 2)))
                start = max(0, min(max_start, start))
                if all(abs(start - existing) >= min_gap for existing in starts):
                    starts.append(start)
                if len(starts) >= clips_count:
                    break

        if len(starts) < clips_count:
            for extra in self._distributed_starts(max_start, clips_count):
                if all(abs(extra - existing) >= min_gap for existing in starts):
                    starts.append(extra)
                if len(starts) >= clips_count:
                    break

        unique_sorted = sorted(set(starts))[:clips_count]
        ranges = [
            (start, min(start + safe_clip_duration, duration))
            for start in unique_sorted
        ]
        return (ranges, duration)

    def _distributed_starts(self, max_start: int, clips_count: int) -> list[int]:
        if clips_count <= 1:
            return [max_start // 2]
        if max_start <= 0:
            return [0 for _ in range(clips_count)]
        intro_offset = int(max_start * 0.08)
        usable_max = max(int(max_start * 0.92), intro_offset)
        return [
            round(intro_offset + ((usable_max - intro_offset) * i) / (clips_count - 1))
            for i in range(clips_count)
        ]

    def _get_source_url(self, video: Video) -> str | None:
        if not video.storage_path:
            return None
        try:
            return VideoWorkerService().get_video_url(
                video.storage_path, expires_in=600
            )
        except Exception as exc:
            logger.warning(f"No se pudo generar URL temporal para analisis: {exc}")
            return None

    def _resolve_video_duration(self, video: Video) -> int | None:
        if video.duration_seconds and video.duration_seconds > 0:
            return int(video.duration_seconds)
        source_url = self._get_source_url(video)
        if not source_url:
            return None
        return self._probe_duration_seconds(source_url)

    def _probe_duration_seconds(self, source_url: str) -> int | None:
        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                source_url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw = result.stdout.strip()
            if not raw:
                return None
            return max(1, int(float(raw)))
        except Exception as exc:
            logger.warning(f"No se pudo obtener duracion con ffprobe: {exc}")
            return None

    def _extract_nonsilent_segments(
        self, source_url: str, duration_sec: int
    ) -> list[tuple[int, int]]:
        try:
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-i",
                source_url,
                "-af",
                "silencedetect=noise=-30dB:d=0.35",
                "-f",
                "null",
                "-",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = f"{result.stdout}\n{result.stderr}"

            nonsilent_segments: list[tuple[int, int]] = []
            active_start = 0.0
            min_segment_len = 1.5

            for line in output.splitlines():
                match_start = re.search(r"silence_start:\s*([0-9]+(?:\.[0-9]+)?)", line)
                if match_start:
                    silence_start = float(match_start.group(1))
                    if silence_start - active_start >= min_segment_len:
                        nonsilent_segments.append(
                            (int(active_start), int(min(silence_start, duration_sec)))
                        )
                    continue

                match_end = re.search(r"silence_end:\s*([0-9]+(?:\.[0-9]+)?)", line)
                if match_end:
                    active_start = float(match_end.group(1))

            if duration_sec - active_start >= min_segment_len:
                nonsilent_segments.append((int(active_start), int(duration_sec)))

            cleaned = [seg for seg in nonsilent_segments if seg[1] > seg[0]]
            return cleaned
        except Exception as exc:
            logger.warning(f"No se pudo analizar silencios para highlights: {exc}")
            return []

    def reframe_video(
        self,
        video_id: UUID,
        user_id: UUID,
        start_sec: int,
        end_sec: int,
        crop_to_vertical: bool | None = None,
        subtitles: bool | None = None,
        face_tracking: bool | None = None,
        color_filter: bool | None = None,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
    ) -> JobReframeResponse:
        video = self._get_user_video(video_id, user_id)

        logger.info(
            "Reframe options for video %s: crop_to_vertical=%s subtitles=%s face_tracking=%s color_filter=%s output_style=%s",
            video_id,
            crop_to_vertical,
            subtitles,
            face_tracking,
            color_filter,
            output_style,
        )

        return self._create_reframe_job(
            video=video,
            user_id=user_id,
            start_sec=start_sec,
            end_sec=end_sec,
            allow_reuse=True,
            output_style=output_style,
        )

    def auto_reframe_video(
        self,
        video_id: UUID,
        user_id: UUID,
        clips_count: int,
        clip_duration_sec: int,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
    ) -> JobAutoReframeResponse:
        video = self._get_user_video(video_id, user_id)
        clip_ranges, used_duration = self._build_auto_clip_ranges(
            video, clips_count, clip_duration_sec
        )

        created_jobs: list[JobAutoReframeItem] = []
        for start_sec, end_sec in clip_ranges:
            job_response = self._create_reframe_job(
                video=video,
                user_id=user_id,
                start_sec=start_sec,
                end_sec=end_sec,
                allow_reuse=False,
                output_style=output_style,
            )
            created_jobs.append(
                JobAutoReframeItem(
                    job_id=job_response.job_id,
                    job_type=job_response.job_type,
                    status=job_response.status,
                    start_sec=job_response.start_sec,
                    end_sec=job_response.end_sec,
                    created_at=job_response.created_at,
                )
            )

        return JobAutoReframeResponse(
            video_id=video.id,
            total_jobs=len(created_jobs),
            clip_duration_sec=clip_duration_sec,
            used_video_duration_sec=used_duration,
            jobs=created_jobs,
        )

    def list_user_clips(
        self, user_id: UUID, limit: int = 20, offset: int = 0, query: str | None = None
    ) -> UserClipsResponse:
        base_query = (
            self.db.query(Job, Video)
            .join(Video, Video.id == Job.video_id)
            .filter(
                Job.user_id == user_id,
                Job.job_type == JobType.REFRAME,
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
                status=job.status,
                output_path=self._resolve_output_url(job.output_path),
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
                Job.job_type == JobType.REFRAME,
            )
            .first()
        )

        if not row:
            raise NotFoundException("Clip no encontrado")

        job, video = row
        clip = UserClipItem(
            job_id=job.id,
            video_id=job.video_id,
            status=job.status,
            output_path=self._resolve_output_url(job.output_path),
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
                Job.job_type == JobType.REFRAME,
            )
            .first()
        )

        if not job:
            raise NotFoundException("Clip no encontrado")

        if job.output_path:
            storage_path = self._extract_storage_path(job.output_path)
            if storage_path:
                VideoWorkerService().delete_video_from_storage(storage_path)

        try:
            self.db.delete(job)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error eliminando clip", str(exc))
