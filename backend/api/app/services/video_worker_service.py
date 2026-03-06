import re
import subprocess

from pathlib import Path
from uuid import UUID, uuid4
from app.core.config import settings
from typing import Literal, Optional, List

from sqlalchemy import String, cast
from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus, JobType
from app.models.video import Video

from app.services.queue_service import QueueService
from app.services.storage_service import StorageService
from app.core.logging import setup_logging
from app.utils.exceptions import (
    NotFoundException,
)

logger = setup_logging()


class VideoWorkerService:
    def __init__(
        self, db: Session, storage_service: StorageService, queue_service: QueueService
    ):
        self.db = db
        self.storage = storage_service
        self.queue = queue_service

    # ==================== AUTO REFRAME CALCS ==========================
    def _build_auto_clip_ranges(
        self,
        video: Video,
        clips_count: int | None,
        clip_duration_sec: int | None,
        requested_profile: Literal["auto", "interview", "sports", "music"],
    ) -> tuple[
        list[tuple[int, int]], int | None, Literal["interview", "sports", "music"]
    ]:
        """
        Depende de:
            _resolve_video_duration
            _get_source_url
            _extract_nonsilent_segments
            _extract_scene_change_timestamps
            _resolve_content_profile
            _resolve_auto_clips_count
            _profile_duration_policy
            _distributed_starts
        """
        duration = self._resolve_video_duration(video)

        source_url = self._get_source_url(video)
        highlights: list[tuple[int, int]] = []
        scene_changes: list[int] = []
        if source_url and duration and duration > 0:
            highlights = self._extract_nonsilent_segments(source_url, duration)
            scene_changes = self._extract_scene_change_timestamps(source_url, duration)

        resolved_profile = self._resolve_content_profile(
            video=video,
            requested_profile=requested_profile,
            duration=duration,
            highlights=highlights,
            scene_changes=scene_changes,
        )

        effective_count = self._resolve_auto_clips_count(duration, clips_count)
        min_len, max_len, default_len = self._profile_duration_policy(resolved_profile)
        preferred_duration = clip_duration_sec or default_len

        if not duration or duration <= 0:
            safe_fallback = max(min_len, min(max_len, preferred_duration))
            starts = [i * safe_fallback for i in range(effective_count)]
            return (
                [(start, start + safe_fallback) for start in starts],
                None,
                resolved_profile,
            )

        safe_clip_duration = min(
            max(min_len, preferred_duration), min(max_len, duration)
        )
        max_start = max(duration - safe_clip_duration, 0)

        if not source_url:
            starts = self._distributed_starts(max_start, effective_count)
            ranges = [
                (start, min(start + safe_clip_duration, duration)) for start in starts
            ]
            return (ranges, duration, resolved_profile)

        starts: list[int] = []
        candidate_ranges: dict[int, tuple[int, int]] = {}
        min_gap = max(1, safe_clip_duration // 2)

        if highlights:
            scored = sorted(highlights, key=lambda seg: seg[1] - seg[0], reverse=True)
            for start_h, end_h in scored:
                segment_len = max(1, end_h - start_h)
                center = (start_h + end_h) / 2
                start = int(round(center - (safe_clip_duration / 2)))
                start = max(0, min(max_start, start))
                if all(abs(start - existing) >= min_gap for existing in starts):
                    dynamic_len = int(round(segment_len * 0.9))
                    dynamic_len = max(min_len, min(max_len, dynamic_len))
                    if resolved_profile == "sports":
                        start, end = self._sports_context_window(
                            anchor=int(round(center)),
                            duration_sec=duration,
                            base_duration=max(dynamic_len, safe_clip_duration),
                            min_len=min_len,
                            max_len=max_len,
                        )
                    else:
                        end = min(start + dynamic_len, duration)

                    starts.append(start)
                    candidate_ranges[start] = (start, end)
                if len(starts) >= effective_count:
                    break

        if len(starts) < effective_count and scene_changes:
            for ts in scene_changes:
                start = int(round(ts - (safe_clip_duration / 2)))
                start = max(0, min(max_start, start))
                if all(abs(start - existing) >= min_gap for existing in starts):
                    if resolved_profile == "sports":
                        start, end = self._sports_context_window(
                            anchor=ts,
                            duration_sec=duration,
                            base_duration=max(safe_clip_duration, 16),
                            min_len=min_len,
                            max_len=max_len,
                        )
                    else:
                        end = min(start + safe_clip_duration, duration)

                    starts.append(start)
                    candidate_ranges[start] = (start, end)
                if len(starts) >= effective_count:
                    break

        if len(starts) < effective_count:
            for extra in self._distributed_starts(max_start, effective_count):
                if all(abs(extra - existing) >= min_gap for existing in starts):
                    starts.append(extra)
                    candidate_ranges[extra] = (
                        extra,
                        min(extra + safe_clip_duration, duration),
                    )
                if len(starts) >= effective_count:
                    break

        unique_sorted = sorted(set(starts))[:effective_count]
        ranges: list[tuple[int, int]] = []
        for start in unique_sorted:
            stored = candidate_ranges.get(start)
            if stored:
                start, end = stored
            else:
                end = min(start + safe_clip_duration, duration)
            if end <= start:
                end = min(duration, start + min_len)
            ranges.append((start, end))

        return (ranges, duration, resolved_profile)

    def _resolve_video_duration(self, video: Video) -> int | None:
        if video.duration_seconds and video.duration_seconds > 0:
            return int(video.duration_seconds)
        source_url = self._get_source_url(video)
        if not source_url:
            return None
        return self._probe_duration_seconds(source_url)

    def _get_source_url(self, video: Video) -> str | None:
        if not video.storage_path:
            return None
        try:
            return self.storage.get_video_url(video.storage_path, expires_in=600)
        except Exception as exc:
            logger.warning(f"No se pudo generar URL temporal para analisis: {exc}")
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

    def _extract_scene_change_timestamps(
        self, source_url: str, duration_sec: int
    ) -> list[int]:
        try:
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-i",
                source_url,
                "-vf",
                "select='gt(scene,0.35)',showinfo",
                "-an",
                "-f",
                "null",
                "-",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = f"{result.stdout}\n{result.stderr}"
            timestamps: list[int] = []
            for line in output.splitlines():
                match = re.search(r"pts_time:([0-9]+(?:\.[0-9]+)?)", line)
                if not match:
                    continue
                ts = int(float(match.group(1)))
                if 0 <= ts <= duration_sec:
                    timestamps.append(ts)
            return sorted(set(timestamps))
        except Exception as exc:
            logger.warning(f"No se pudo detectar cambios de escena: {exc}")
            return []

    def _resolve_content_profile(
        self,
        *,
        video: Video,
        requested_profile: Literal["auto", "interview", "sports", "music"],
        duration: int | None,
        highlights: list[tuple[int, int]],
        scene_changes: list[int],
    ) -> Literal["interview", "sports", "music"]:
        if requested_profile != "auto":
            return requested_profile

        filename = (video.original_filename or "").lower()
        sports_keywords = ["gol", "football", "futbol", "soccer", "liga", "vs", "match"]
        music_keywords = [
            "music",
            "musica",
            "song",
            "live",
            "lyrics",
            "concierto",
            "karaoke",
        ]

        if any(key in filename for key in sports_keywords):
            return "sports"
        if any(key in filename for key in music_keywords):
            return "music"

        if not duration or duration <= 0:
            return "interview"

        nonsilent_seconds = sum(max(0, end - start) for start, end in highlights)
        nonsilent_ratio = nonsilent_seconds / duration if duration > 0 else 0
        scenes_per_min = (len(scene_changes) / max(duration, 1)) * 60

        if scenes_per_min >= 18 and nonsilent_ratio >= 0.45:
            return "sports"
        if nonsilent_ratio >= 0.8 and scenes_per_min <= 12:
            return "music"
        return "interview"

    def _resolve_auto_clips_count(
        self, duration: int | None, requested: int | None
    ) -> int:
        if requested is not None:
            return requested
        if not duration:
            return 3
        if duration < 90:
            return 2
        if duration < 300:
            return 3
        if duration < 900:
            return 4
        return 5

    def _profile_duration_policy(
        self, profile: Literal["interview", "sports", "music"]
    ) -> tuple[int, int, int]:
        if profile == "sports":
            return (8, 22, 14)
        if profile == "music":
            return (12, 32, 20)
        return (8, 20, 14)

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

    def _sports_context_window(
        self,
        *,
        anchor: int,
        duration_sec: int,
        base_duration: int,
        min_len: int,
        max_len: int,
    ) -> tuple[int, int]:
        # En deportes priorizamos contexto previo a la accion (pre-jugada + gol/reaccion).
        target_len = max(min_len, min(max_len, max(base_duration, 16)))
        pre_ratio = 0.62
        pre = int(round(target_len * pre_ratio))
        post = max(1, target_len - pre)

        start = max(0, anchor - pre)
        end = min(duration_sec, anchor + post)

        current_len = end - start
        if current_len < min_len:
            missing = min_len - current_len
            extend_right = min(missing, max(0, duration_sec - end))
            end += extend_right
            missing -= extend_right
            if missing > 0:
                start = max(0, start - missing)

        return (start, end)

    # ==================== JOB PERSISTENCE ==========================
    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        error_message: str | None = None,
        video_path: Optional[str] = None,
        subtitles_path: Optional[str] = None,
        child_jobs: Optional[List[str]] = None,
    ) -> bool:
        try:
            job = self.db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.warning(f"❌ Job {job_id} not found in DB for status update")
                return False

            existing = job.output_path or {}

            existing.update(
                {
                    k: v
                    for k, v in {
                        "video": video_path,
                        "subtitles": subtitles_path,
                        "jobs": child_jobs,
                    }.items()
                    if v is not None
                }
            )

            job.status = status
            job.error_message = error_message or None
            job.output_path = existing or None

            self.db.commit()
            return True

        except Exception as exc:
            self.db.rollback()
            logger.error(f"❌ Could not persist state for job {job_id}: {exc}")
            return False

    def get_by_id(self, job_id: UUID) -> Job | None:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundException("Job not found")
        return job

    def create_reframe_job_for_worker(
        self,
        user_id: UUID,
        video_id: UUID,
        start_sec: int,
        end_sec: int,
        watermark: str,
        subtitles: bool,
        output_style: Literal["vertical", "speaker_split"] = "vertical",
        content_profile: Literal["auto", "interview", "sports", "music"] = "auto",
        job_type: JobType = JobType.REFRAME,
    ) -> Job:
        """
        Crea un job en la DB y lo publica en Redis sin generar
        ninguna respuesta para un controller.
        """
        # Persistir job en DB
        job = Job(
            user_id=user_id,
            video_id=video_id,
            job_type=job_type,
            status=JobStatus.PENDING,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Publicar en Redis
        try:
            self.queue.publish_reframe_job(
                job_id=str(job.id),
                video_id=str(video_id),
                user_id=str(user_id),
                start_sec=start_sec,
                end_sec=end_sec,
                watermark=watermark,
                subtitles=subtitles,
                output_style=output_style,
                content_profile=content_profile,
            )
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = "Error enviando job a la cola"
            self.db.commit()
            raise e

        return job
