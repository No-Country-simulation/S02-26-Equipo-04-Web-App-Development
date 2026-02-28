from uuid import UUID, uuid4
from pathlib import Path

import re

from fastapi import UploadFile
from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.models.enums import VideoStatus

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.storage_service import StorageService

from app.services.job_service import JobService
from app.models.enums import JobStatus, JobType
from app.models.job import Job

from app.models.video import Video


from app.schemas.video import (
    VideoFromJobResponse,
    UpdateVideoRequest,
    UserVideoDetailResponse,
    VideoUploadResponse,
    VideoURLResponse,
    UserVideoItem,
    UserVideosResponse,
)
from app.utils.exceptions import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
    VideoDBException,
    VideoValidationException,
    VideoConflictException
)

MAX_FILENAME_LENGTH = 255
FILENAME_REGEX = r"^[\w\-. ]+$"  # letras, números, _, -, ., espacio

logger = setup_logging()


class VideoService:
    """Servicio de videos - Maneja validación, almacenamiento y metadata"""

    # Configuración de validación
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"mp4", "mkv", "avi", "mov", "flv", "wmv", "webm", "m4v"}
    ALLOWED_MIME_TYPES = {
        "video/mp4",
        "video/x-matroska",
        "video/x-msvideo",
        "video/quicktime",
        "video/x-flv",
        "video/x-ms-wmv",
        "video/webm",
    }


    def __init__(self, db: Session, storage_service: StorageService):
        self.db = db
        self.storage = storage_service


    def _validate_file(self, file: UploadFile) -> int:
        """
        Valida el archivo subido.

        Args:
            file: Archivo subido

        Returns:
            Tamaño del archivo en bytes

        Raises:
            VideoValidationException: Si el archivo no cumple los requisitos
        """
        # Validar nombre
        if not file.filename:
            raise VideoValidationException("El archivo debe tener un nombre")

        # Validar extensión
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise VideoValidationException(
                f"Extensión no permitida. Extensiones válidas: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )

        # Validar MIME type
        if file.content_type:
            if file.content_type not in self.ALLOWED_MIME_TYPES:
                if (
                    file.content_type == "application/octet-stream"
                    and ext in self.ALLOWED_EXTENSIONS
                ):
                    logger.info(
                        "MIME type generico application/octet-stream aceptado por extension valida '%s'",
                        ext,
                    )
                else:
                    raise VideoValidationException(
                        f"Tipo de archivo no válido. MIME type: {file.content_type}"
                    )

        # Obtener tamaño
        try:
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
            file.file.seek(0)
        except Exception:
            raise VideoValidationException(
                "No se pudo determinar el tamaño del archivo"
            )

        # Validar tamaño no vacío
        if size_bytes == 0:
            raise VideoValidationException("El archivo está vacío")

        # Validar tamaño máximo
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise VideoValidationException(
                f"El archivo excede el tamaño máximo permitido ({max_mb}MB)"
            )

        return size_bytes


    def _get_user_video(self, video_id: UUID, user_id: UUID) -> Video:
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise NotFoundException(f"Video con ID {video_id} no encontrado")
        if video.user_id != user_id:
            raise ForbiddenException("No tienes permisos para acceder a este video")
        return video


    def _to_user_video_item(self, video: Video) -> UserVideoItem:
        return UserVideoItem(
            video_id=video.id,
            filename=video.original_filename,
            status=video.status,
            uploaded_at=video.created_at,
            preview_url=self._build_preview_url(video),
        )


    def _build_preview_url(self, video: Video, expires_in: int = 3600) -> str | None:
        if not video.storage_path:
            return None
        try:
            return self.storage.get_video_public_url(
                video.storage_path, expires_in=expires_in
            )

        except Exception as exc:
            logger.warning(
                f"Error generando URL de preview para video {video.id}: {exc}"
            )
            raise VideoValidationException(
                "No se pudo generar la URL de preview", str(exc)
            )


    def create_video_from_job(self, job: Job, user_id: UUID) -> VideoFromJobResponse:
        """
        Crea un video en base al output de un Job
        """

        if not job.user_id == user_id:
            raise ForbiddenException("job_id no corresponde al Usuario")
        if job.status != JobStatus.DONE:
            raise VideoConflictException("Job debe tener status DONE para crear un Video")
        if job.job_type == JobType.AUTO_REFRAME:
            raise VideoConflictException("Job AUTO_REFRAME tiene multiples videos, usar un Job type REFRAME")


        storage_path = (job.output_path or {}).get("video")
        if not storage_path:
            raise VideoConflictException("Job output video not found")
        
        if not self.storage.exists(storage_path):
            raise VideoConflictException("Job output video missing in storage")
        bucket, object_key = self.storage._extract_bucket_and_key(storage_path)
        
        filename = job.video.original_filename
        if not filename:
            raise VideoConflictException("Video has no original filename")

        
        try:
            video = Video(
                user_id=user_id,
                original_filename=filename,
                storage_path=storage_path,
                status=VideoStatus.AVAILABLE,
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
        except Exception as exc:
            raise VideoDBException("Error guardando Video desde Job en DB", str(exc))

        return VideoFromJobResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=filename,
            user_id=user_id,
            storage_path=video.storage_path,
            uploaded_at=video.created_at,
        )


    def upload_video_authenticated(
        self, file: UploadFile, user_id: UUID
    ) -> VideoUploadResponse:
        """
        Sube un video asociado a un usuario autenticado.

        Args:
            file: Archivo subido
            user_id: ID del usuario

        Returns:
            VideoUploadResponse con información del video subido

        Raises:
            VideoValidationException: Si el archivo no es válido
            MinIOStorageException: Si falla la subida a MinIO
            VideoDBException: Si falla guardar en base de datos
        """
        size_bytes = self._validate_file(file)

        storage_path, bucket, object_key = self.storage.upload_fileobj_to_minio(
            file.file, file.filename
        )

        # Crear registro en DB/commit
        try:
            video = Video(
                user_id=user_id,
                original_filename=file.filename,
                storage_path=storage_path,
                status=VideoStatus.PENDING_METADATA,
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
        except Exception as exc:
            try:
                self.storage.delete_video_from_storage(storage_path)
            except Exception:
                pass
            raise VideoDBException("Error guardando video en DB", str(exc))

        return VideoUploadResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            user_id=user_id,
            storage_path=video.storage_path,
            uploaded_at=video.created_at,
        )


    def get_video_url(self, video_id: UUID, expires_in: int = 3600) -> VideoURLResponse:
        """
        Genera una URL presignada para descargar el video.

        Args:
            video_id: ID del video
            expires_in: Tiempo de expiración en segundos (default: 1 hora)

        Returns:
            VideoURLResponse con la URL presignada

        Raises:
            HTTPException: Si el video no existe o no tiene storage_path
            MinIOStorageException: Si falla la generación de URL
        """
        # Buscar el video en la DB
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise NotFoundException(f"Video con ID {video_id} no encontrado")

        if not video.storage_path:
            raise BadRequestException(
                "El video no tiene una ruta de almacenamiento válida"
            )

        url = self.storage.get_video_public_url(
            video.storage_path, expires_in=expires_in
        )

        return VideoURLResponse(
            video_id=video.id,
            url=url,
            expires_in_seconds=expires_in,
            filename=video.original_filename,
        )


    def list_user_videos(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        query: str | None = None,
    ) -> UserVideosResponse:
        base_query = self.db.query(Video).filter(Video.user_id == user_id)

        cleaned_query = (query or "").strip()
        if cleaned_query:
            like_term = f"%{cleaned_query}%"
            base_query = base_query.filter(
                (Video.original_filename.ilike(like_term))
                | (cast(Video.id, String).ilike(like_term))
            )

        total = base_query.count()
        rows = (
            base_query.order_by(Video.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        videos: list[UserVideoItem] = []
        for video in rows:
            videos.append(self._to_user_video_item(video))

        return UserVideosResponse(
            total=total, limit=limit, offset=offset, videos=videos
        )


    def get_user_video(self, video_id: UUID, user_id: UUID) -> UserVideoDetailResponse:
        video = self._get_user_video(video_id, user_id)
        return UserVideoDetailResponse(
            video_id=video.id,
            filename=video.original_filename,
            status=video.status,
            uploaded_at=video.created_at,
            updated_at=video.updated_at,
            storage_path=video.storage_path,
            preview_url=self._build_preview_url(video),
        )


    def update_user_video(
        self, video_id: UUID, user_id: UUID, payload: UpdateVideoRequest
    ) -> UserVideoItem:
        """
        Actualiza el nombre visible del video preservando la extensión original.

        - El usuario solo envía el nombre base (sin extensión).
        - La extensión original se conserva automáticamente.
        - No modifica el objeto físico en MinIO.
        """
        video = self._get_user_video(video_id, user_id)

        base_name = payload.filename.strip()

        # 1️⃣ No vacío
        if not base_name:
            raise VideoValidationException("El nombre de archivo no puede estar vacío")

        # 2️⃣ Longitud máxima
        if len(base_name) > MAX_FILENAME_LENGTH:
            raise VideoValidationException(
                f"El nombre no puede superar los {MAX_FILENAME_LENGTH} caracteres"
            )

        # 3️⃣ Caracteres permitidos
        if not re.match(FILENAME_REGEX, base_name):
            raise VideoValidationException("El nombre contiene caracteres inválidos")

        # 4️⃣ Conservar extensión original
        original_ext = Path(video.original_filename).suffix
        new_filename = f"{base_name}{original_ext}"

        try:
            video.original_filename = new_filename
            self.db.commit()
            self.db.refresh(video)
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException(
                "Error cambiando el nombre del archivo",
                str(exc),
            )

        return self._to_user_video_item(video)


    def delete_user_video(self, video_id: UUID, user_id: UUID) -> None:
        video = self._get_user_video(video_id, user_id)

        if not video.storage_path:
            raise BadRequestException(
                "El video no tiene una ruta de almacenamiento válida"
            )

        try:
            self.db.delete(video)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error eliminando video", str(exc))
        
        # Luego eliminar de MinIO
        if video.storage_path:
            try:
                self.storage.delete_video_from_storage(video.storage_path)
            except Exception:
                logger.warning(
                    f"Audio {video.id} removed from DB but still exists in storage"
                )