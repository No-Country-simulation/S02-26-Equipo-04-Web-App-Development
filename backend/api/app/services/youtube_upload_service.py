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
            resolved_title = title or job.video.original_filename or f"Clip {str(job_id)[:8]}"
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
            return {"connected": False, "message": "Usuario no tiene cuenta de YouTube conectada"}

        return {
            "connected": True,
            "provider_username": oauth_token.provider_username,
            "provider_user_id": oauth_token.provider_user_id,
            "token_expires_at": (
                oauth_token.expires_at.isoformat() if oauth_token.expires_at else None
            ),
            "is_expired": oauth_token.is_expired(),
        }

   
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
            raise BadRequestException(
                f"Error descargando video de MinIO: {exc}"
            )

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
            oauth_token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            oauth_token.last_refreshed_at = datetime.now(timezone.utc)
            self.db.commit()

            logger.info("✅ Token renovado exitosamente")
            return new_access_token
