"""
Servicio para publicar videos procesados en YouTube.

Usa YouTube Data API v3 con OAuth2.
Toda la lógica de negocio de publicación vive aquí;
el controlador solo delega y devuelve respuestas HTTP.
"""

import asyncio
import json
import logging
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.oauth_token import OAuthToken
from app.services.storage_service import StorageService
from app.utils.exceptions import (
    BadRequestException,
    NotFoundException,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
APP_NAME = "Hacelo Corto"
YOUTUBE_CATEGORY_PEOPLE_BLOGS = "22"
DEFAULT_DESCRIPTION_TEMPLATE = "Clip generado con Hacelo Corto"


class YouTubeUploadService:
    """
    Servicio para manejar la publicación de clips procesados en YouTube.

    Responsabilidades:
    - Validar que el Job exista y pertenezca al usuario.
    - Extraer la ruta del video desde ``job.output_path`` (JSON).
    - Descargar el video de MinIO a un archivo temporal (requerido por
      ``MediaFileUpload`` de la YouTube API).
    - Subir el video a YouTube con metadata configurada.
    - Renovar tokens OAuth expirados de forma transparente.
    """

    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(
        self,
        db: Session,
        storage_service: StorageService,
    ) -> None:
        self.db = db
        self.storage = storage_service

    # ------------------------------------------------------------------
    #  Método principal — orquesta toda la publicación
    # ------------------------------------------------------------------
    async def publish_job_to_youtube(
        self,
        *,
        job_id: UUID,
        user_id: UUID,
        title: str | None = None,
        description: str | None = None,
        privacy: str = "private",
    ) -> Dict[str, Any]:
        """
        Publica el video procesado de un Job en YouTube.

        Args:
            job_id: ID del Job que contiene el clip procesado.
            user_id: ID del usuario autenticado (para validar pertenencia).
            title: Título del video en YouTube (se toma del nombre original
                   si no se provee).
            description: Descripción del video en YouTube.
            privacy: ``"public"``, ``"private"`` o ``"unlisted"``.

        Returns:
            Diccionario con la información del video publicado.

        Raises:
            NotFoundException: Si el Job no existe.
            BadRequestException: Si el Job no pertenece al usuario, no está
                terminado, o el usuario no tiene YouTube conectado.
        """
        # 1. Buscar y validar el Job
        job = self._get_validated_job(job_id, user_id)

        # 2. Extraer ruta del video desde output_path (JSON)
        video_storage_path = self._extract_video_path(job)

        # 3. Descargar video de MinIO a archivo temporal
        #    (YouTube API requiere archivo local para MediaFileUpload)
        temp_path = await self._download_to_temp(video_storage_path)

        try:
            # 4. Preparar metadata
            resolved_title = (
                title or job.video.original_filename or f"Clip {str(job_id)[:8]}"
            )
            resolved_description = description or f"Video generado con {APP_NAME}"
            tags = self._build_tags(job)

            # 5. Subir a YouTube
            result = await self._upload_to_youtube(
                user_id=user_id,
                video_file_path=temp_path,
                title=resolved_title,
                description=resolved_description,
                tags=tags,
                privacy_status=privacy,
            )

            logger.info(" Video publicado en YouTube: %s", result["video_url"])

            return {
                "success": True,
                "message": "Video publicado en YouTube exitosamente",
                "job_id": str(job_id),
                "youtube_video_id": result["video_id"],
                "youtube_url": result["video_url"],
                "title": result["title"],
                "privacy": result["privacy_status"],
                "thumbnail_url": result.get("thumbnail_url"),
            }
        finally:
            # 6. Garantizar limpieza del archivo temporal
            self._cleanup_temp(temp_path)

    # ------------------------------------------------------------------
    #  Consultar estado de conexión YouTube
    # ------------------------------------------------------------------
    def get_connection_status(self, user_id: UUID) -> Dict[str, Any]:
        """Devuelve si el usuario tiene su cuenta de YouTube conectada."""
        oauth_token = self._find_youtube_token(user_id)

        if not oauth_token:
            return {
                "connected": False,
                "message": "Usuario no tiene cuenta de YouTube conectada",
            }

        return {
            "connected": True,
            "provider_username": oauth_token.provider_username,
            "provider_user_id": oauth_token.provider_user_id,
            "token_expires_at": (
                oauth_token.expires_at.isoformat() if oauth_token.expires_at else None
            ),
            "is_expired": oauth_token.is_expired(),
        }

    async def suggest_metadata_for_job(
        self,
        *,
        job_id: UUID,
        user_id: UUID,
        tone: str = "neutral",
    ) -> Dict[str, Any]:
        """Genera sugerencias de titulo/descripcion/hashtags para YouTube."""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundException(f"Job {job_id} no encontrado")

        if job.user_id != user_id:
            raise BadRequestException(
                "No tenes permiso para generar metadata de este clip"
            )

        source_name = "clip"
        if job.video and job.video.original_filename:
            source_name = job.video.original_filename

        subtitle_excerpt = self._extract_subtitle_excerpt(job)
        base_title = self._build_default_title(source_name, str(job.id))
        base_description = self._build_default_description(
            source_name,
            subtitle_excerpt,
            tone,
        )

        metadata = self._fallback_metadata(base_title, base_description)
        metadata["provider"] = "template"
        metadata["generated_with_ai"] = False

        if not settings.OPENROUTER_API_KEY:
            return metadata

        ai_metadata = await self._generate_metadata_with_openrouter(
            source_filename=source_name,
            job_id=str(job.id),
            subtitle_excerpt=subtitle_excerpt,
            tone=tone,
            fallback=metadata,
        )
        return ai_metadata

    #  Métodos privados — lógica interna

    def _get_validated_job(self, job_id: UUID, user_id: UUID) -> Job:
        """Busca el Job, valida pertenencia y estado DONE."""
        job = self.db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise NotFoundException(f"Job {job_id} no encontrado")

        if job.user_id != user_id:
            raise BadRequestException("No tenés permiso para publicar este clip")

        if job.status != JobStatus.DONE:
            raise BadRequestException(
                f"El clip aún no está listo. Estado actual: {job.status.value}"
            )

        if job.output_path is None:
            raise BadRequestException("El Job no tiene un video de salida")

        return job

    def _extract_video_path(self, job: Job) -> str:
        """
        Extrae la ruta S3 del video desde ``job.output_path``.

        ``output_path`` puede ser:
        - Un JSON ``{"video": "s3://...", "subtitles": "s3://..."}``
        - Un string directo ``"s3://..."`` (compatibilidad hacia atrás)
        """
        raw = job.output_path

        # Intentar parsear como JSON
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, dict):
                video_path = parsed.get("video")
                if video_path:
                    return video_path
                # Si no tiene clave "video", podría ser otro formato
                raise BadRequestException(
                    "output_path JSON no contiene la clave 'video'"
                )
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: output_path es un string directo (formato legacy)
        if isinstance(raw, str) and raw.startswith("s3://"):
            return raw

        raise BadRequestException(f"Formato de output_path no reconocido: {raw}")

    async def _download_to_temp(self, storage_path: str) -> str:
        """
        Descarga un archivo de MinIO a un temporal local.

        Necesario porque la YouTube API (``MediaFileUpload``) requiere
        un path a un archivo en disco; no acepta URLs externas.

        Usa ``asyncio.to_thread`` para no bloquear el event loop
        durante la descarga (boto3 es síncrono).
        """
        bucket, key = self.storage._extract_bucket_and_key(storage_path)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_path = temp_file.name
        temp_file.close()

        logger.info(" Descargando video de MinIO: bucket=%s key=%s", bucket, key)

        try:
            await asyncio.to_thread(
                self.storage.client.download_file,
                Bucket=bucket,
                Key=key,
                Filename=temp_path,
            )
        except Exception as exc:
            self._cleanup_temp(temp_path)
            raise BadRequestException(f"Error descargando video de MinIO: {exc}")

        logger.info("✅ Video descargado a: %s", temp_path)
        return temp_path

    @staticmethod
    def _build_tags(job: Job) -> list[str]:
        """Genera tags basados en las características del video."""
        tags = ["hacelocorto", "ai", "shorts"]
        video = job.video
        if video and video.width and video.height and video.height > video.width:
            tags.append("vertical")
        return tags

    def _extract_subtitle_excerpt(self, job: Job) -> str:
        raw_output = job.output_path
        if not isinstance(raw_output, dict):
            return ""

        subtitles_path = raw_output.get("subtitles")
        if not isinstance(subtitles_path, str) or not subtitles_path.startswith(
            "s3://"
        ):
            return ""

        try:
            bucket, key = self.storage._extract_bucket_and_key(subtitles_path)
            response = self.storage.client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
            text = body.decode("utf-8", errors="ignore")
        except Exception:
            return ""

        lines: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.isdigit():
                continue
            if "-->" in line:
                continue
            lines.append(line)
            if len(lines) >= 4:
                break

        return " ".join(lines)[:500]

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        cleaned = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", filename)
        cleaned = re.sub(r"[_\-]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "clip"

    def _build_default_title(self, source_filename: str, job_id: str) -> str:
        stem = self._sanitize_filename(source_filename)
        title = f"{stem} | Clip corto"
        if len(title) > 100:
            title = title[:97].rstrip() + "..."
        if not title.strip():
            title = f"Clip {job_id[:8]} - {APP_NAME}"
        return title

    @staticmethod
    def _build_default_description(
        source_filename: str,
        subtitle_excerpt: str,
        tone: str,
    ) -> str:
        source = f"Fuente: {source_filename}" if source_filename else ""
        tone_line = {
            "energetic": "Tono: dinamico y potente.",
            "informative": "Tono: informativo y claro.",
        }.get(tone, "Tono: neutral y directo.")
        parts = [DEFAULT_DESCRIPTION_TEMPLATE]
        parts.append(tone_line)
        if subtitle_excerpt:
            parts.append(f"Momento destacado: {subtitle_excerpt}")
        if source:
            parts.append(source)
        parts.append("#shorts #hacelocorto")
        return "\n".join(parts)[:5000]

    @staticmethod
    def _normalize_hashtags(values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            token = value.strip()
            if not token:
                continue
            token = token.replace(" ", "")
            if not token.startswith("#"):
                token = f"#{token}"
            token = re.sub(r"[^#\w]", "", token)
            if len(token) <= 1:
                continue
            lowered = token.lower()
            if lowered in {item.lower() for item in normalized}:
                continue
            normalized.append(token)
            if len(normalized) >= 10:
                break
        return normalized

    @staticmethod
    def _normalize_tags(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            token = value.strip().lstrip("#")
            token = re.sub(r"\s+", " ", token)
            if not token:
                continue
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(token[:50])
            if len(normalized) >= 15:
                break
        return normalized

    def _fallback_metadata(self, title: str, description: str) -> Dict[str, Any]:
        hashtags = self._normalize_hashtags(
            ["#shorts", "#hacelocorto", "#clip", "#video"]
        )
        tags = self._normalize_tags([item.lstrip("#") for item in hashtags])
        return {
            "title": title[:100],
            "description": description[:5000],
            "hashtags": hashtags,
            "tags": tags,
        }

    @staticmethod
    def _extract_json_object(raw_text: str) -> Dict[str, Any] | None:
        candidate = raw_text.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
            candidate = re.sub(r"```$", "", candidate).strip()

        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None

    async def _generate_metadata_with_openrouter(
        self,
        *,
        source_filename: str,
        job_id: str,
        subtitle_excerpt: str,
        tone: str,
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        tone_hint = {
            "neutral": "Tono neutral y claro.",
            "energetic": "Tono energico y dinamico, sin exageraciones.",
            "informative": "Tono informativo y directo.",
        }.get(tone, "Tono neutral y claro.")

        prompt = (
            "Genera metadata para YouTube Shorts en español rioplatense. "
            "Responde SOLO JSON valido con claves: title, description, hashtags, tags. "
            "title max 100 chars. description max 5000 chars. "
            "hashtags array de 5 a 10 items (con #). tags array de 5 a 12 items (sin #). "
            "Evita promesas engañosas.\n"
            f"job_id: {job_id}\n"
            f"source_filename: {source_filename}\n"
            f"subtitle_excerpt: {subtitle_excerpt or 'sin subtitulos'}\n"
            f"tono: {tone_hint}"
        )

        body = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres especialista en copy para YouTube Shorts. Devuelves JSON estricto.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.5,
        }

        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=25) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()

            message = (
                payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            parsed = self._extract_json_object(message)
            if not parsed:
                return {
                    **fallback,
                    "provider": f"openrouter:{settings.OPENROUTER_MODEL}",
                    "generated_with_ai": False,
                }

            raw_hashtags = parsed.get("hashtags")
            raw_tags = parsed.get("tags")
            hashtags = raw_hashtags if isinstance(raw_hashtags, list) else []
            tags = raw_tags if isinstance(raw_tags, list) else []

            title = str(parsed.get("title") or fallback["title"]).strip()[:100]
            description = str(
                parsed.get("description") or fallback["description"]
            ).strip()[:5000]

            normalized_hashtags = self._normalize_hashtags(
                [str(item) for item in hashtags]
            )
            if not normalized_hashtags:
                normalized_hashtags = fallback["hashtags"]

            normalized_tags = self._normalize_tags([str(item) for item in tags])
            if not normalized_tags:
                normalized_tags = fallback["tags"]

            return {
                "title": title,
                "description": description,
                "hashtags": normalized_hashtags,
                "tags": normalized_tags,
                "provider": f"openrouter:{settings.OPENROUTER_MODEL}",
                "generated_with_ai": True,
            }
        except Exception as exc:
            logger.warning("No se pudo generar metadata con OpenRouter: %s", exc)
            return {
                **fallback,
                "provider": f"openrouter:{settings.OPENROUTER_MODEL}",
                "generated_with_ai": False,
            }

    @staticmethod
    def _cleanup_temp(path: str) -> None:
        """Elimina un archivo temporal de forma segura."""
        try:
            if path and os.path.exists(path):
                os.unlink(path)
                logger.info("🗑️ Archivo temporal eliminado: %s", path)
        except OSError as exc:
            logger.warning("⚠️ No se pudo eliminar archivo temporal: %s", exc)

    # ------------------------------------------------------------------
    #  YouTube API — upload
    # ------------------------------------------------------------------
    async def _upload_to_youtube(
        self,
        *,
        user_id: UUID,
        video_file_path: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str,
        category_id: str = YOUTUBE_CATEGORY_PEOPLE_BLOGS,
    ) -> Dict[str, Any]:
        """Sube un archivo de video a YouTube usando la API oficial."""

        access_token = await self._get_valid_access_token(user_id)

        credentials = Credentials(
            token=access_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )

        youtube = build("youtube", "v3", credentials=credentials)

        body: Dict[str, Any] = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        logger.info("📤 Subiendo '%s' a YouTube (user_id=%s)", title, user_id)
        logger.info(
            "📁 Archivo: %s (%d bytes)",
            video_file_path,
            os.path.getsize(video_file_path),
        )

        media = MediaFileUpload(
            video_file_path,
            mimetype="video/*",
            resumable=True,
            chunksize=1024 * 1024,  # 1 MB chunks
        )

        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        # Upload con progreso — envuelto en asyncio.to_thread porque
        # next_chunk() es bloqueante y puede tardar minutos.
        def _do_upload():
            resp = None
            while resp is None:
                status_obj, resp = insert_request.next_chunk()
                if status_obj:
                    progress = int(status_obj.progress() * 100)
                    logger.info("📊 Upload progress: %d%%", progress)
            return resp

        response = await asyncio.to_thread(_do_upload)

        video_id = response.get("id")

        return {
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "title": response["snippet"]["title"],
            "privacy_status": response["status"]["privacyStatus"],
            "thumbnail_url": (
                response.get("snippet", {})
                .get("thumbnails", {})
                .get("default", {})
                .get("url")
            ),
        }

    # ------------------------------------------------------------------
    #  OAuth — gestión de tokens
    # ------------------------------------------------------------------
    def _find_youtube_token(self, user_id: UUID) -> OAuthToken | None:
        """Busca el token OAuth de YouTube del usuario."""
        return (
            self.db.query(OAuthToken)
            .filter(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == "youtube",
            )
            .first()
        )

    async def _get_valid_access_token(self, user_id: UUID) -> str:
        """
        Obtiene un access token válido para YouTube.
        Si está expirado, lo renueva automáticamente.
        """
        oauth_token = self._find_youtube_token(user_id)

        if not oauth_token:
            raise BadRequestException(
                "Usuario no tiene cuenta de YouTube conectada. "
                "Debe hacer login con Google primero."
            )

        if not oauth_token.is_expired():
            return oauth_token.access_token

        logger.info("🔄 Token expirado, renovando para user_id=%s", user_id)

        if not oauth_token.refresh_token:
            raise BadRequestException(
                "No hay refresh token. El usuario debe reconectar su cuenta de YouTube."
            )

        return await self._refresh_access_token(oauth_token)

    async def _refresh_access_token(self, oauth_token: OAuthToken) -> str:
        """Renueva el access token usando el refresh token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": oauth_token.refresh_token,
                    "grant_type": "refresh_token",
                },
            )

            if response.status_code != 200:
                logger.error("❌ Error renovando token: %s", response.text)
                raise BadRequestException("Error al renovar token de YouTube")

            token_data = response.json()
            new_access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)

            # Persistir token renovado
            oauth_token.access_token = new_access_token
            oauth_token.expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in
            )
            oauth_token.last_refreshed_at = datetime.now(timezone.utc)
            self.db.commit()

            logger.info("✅ Token renovado exitosamente")
            return new_access_token
