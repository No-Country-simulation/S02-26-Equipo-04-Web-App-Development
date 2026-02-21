from datetime import datetime
from uuid import UUID, uuid4
from fastapi import UploadFile
from sqlalchemy import String, cast
from sqlalchemy.orm import Session
import boto3
import subprocess
import json
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.video import Video
from app.schemas.video import (
    UpdateVideoRequest,
    UserVideoDetailResponse,
    VideoUploadResponse,
    VideoURLResponse,
    UserVideoItem,
    UserVideosResponse,
)
from app.utils.exceptions import (
    BadRequestException,
    MinIOStorageException,
    NotFoundException,
    ForbiddenException,
    VideoDBException,
    VideoValidationException,
)


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

    def __init__(self, db: Session):
        self.db = db

    def _get_s3_client(self, endpoint: str | None = None, secure: bool | None = None):
        """Obtiene cliente S3 configurado para MinIO"""
        selected_endpoint = endpoint or settings.MINIO_ENDPOINT
        selected_secure = settings.MINIO_SECURE if secure is None else secure
        scheme = "https" if selected_secure else "http"
        endpoint_url = f"{scheme}://{selected_endpoint}"
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _ensure_bucket_exists(self, s3_client, bucket: str) -> None:
        """
        Crea el bucket si no existe.

        Raises:
            MinIOStorageException: Si no se puede verificar/crear el bucket
        """
        try:
            s3_client.head_bucket(Bucket=bucket)
        except ClientError as exc:
            try:
                s3_client.create_bucket(Bucket=bucket)
            except ClientError as create_exc:
                raise MinIOStorageException(
                    f"Error creando bucket '{bucket}'", str(create_exc)
                )

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

    def _create_video_record(
        self, original_filename: str, user_id: UUID | None
    ) -> Video:
        """
        Crea un registro de video en la base de datos.

        Args:
            original_filename: Nombre original del archivo
            user_id: ID del usuario (None para uploads públicos)

        Returns:
            Video creado

        Raises:
            VideoDBException: Si falla la creación del registro
        """
        try:
            video = Video(
                user_id=user_id,
                original_filename=original_filename,
                storage_path=None,
                status="uploaded",
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            return video
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error creando registro de video", str(exc))

    def _extract_metadata(self, storage_path: str) -> dict:
        try:
            bucket, object_key = self._extract_bucket_and_key(storage_path)
            s3_client = self._get_s3_client()
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=3600,
            )
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                presigned_url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {}
            return json.loads(result.stdout) if result.stdout else {}
        except Exception:
            return {}

    def _save_metadata_to_video(self, video: Video, metadata: dict) -> None:
        try:
            if metadata.get("format"):
                video.duration_seconds = int(
                    float(metadata["format"].get("duration", 0))
                )

            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video":
                    fps_str = stream.get("r_frame_rate", "0")
                    if fps_str and "/" in str(fps_str):
                        fps_value = float(fps_str.split("/")[0])
                        video.fps = int(fps_value)
                    video.width = stream.get("width")
                    video.height = stream.get("height")
                    video.codec = stream.get("codec_name")
                    video.bitrate = stream.get("bit_rate")
                elif stream.get("codec_type") == "audio":
                    video.has_audio = True
                    video.audio_codec = stream.get("codec_name")

            self.db.commit()
        except Exception:
            self.db.rollback()

    def _extract_bucket_and_key(self, storage_path: str) -> tuple[str, str]:
        cleaned_path = storage_path.replace("s3://", "")
        parts = cleaned_path.split("/", 1)
        if len(parts) != 2:
            raise BadRequestException("Formato de storage_path inválido")
        return (parts[0], parts[1])

    def _build_preview_url(self, video: Video, expires_in: int = 3600) -> str | None:
        if not video.storage_path:
            return None
        try:
            return self.get_video_url(video.id, expires_in=expires_in).url
        except Exception:
            return None

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
        video = self._get_user_video(video_id, user_id)
        cleaned_filename = payload.filename.strip()
        if not cleaned_filename:
            raise BadRequestException("El nombre de archivo no puede estar vacío")

        try:
            video.original_filename = cleaned_filename
            self.db.commit()
            self.db.refresh(video)
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error actualizando metadata del video", str(exc))

        return self._to_user_video_item(video)

    def delete_user_video(self, video_id: UUID, user_id: UUID) -> None:
        video = self._get_user_video(video_id, user_id)

        if video.storage_path:
            bucket, object_key = self._extract_bucket_and_key(video.storage_path)
            s3_client = self._get_s3_client()
            try:
                s3_client.delete_object(Bucket=bucket, Key=object_key)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code not in {"NoSuchKey", "404"}:
                    raise MinIOStorageException(
                        "Error eliminando archivo de MinIO", str(exc)
                    )

        try:
            self.db.delete(video)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error eliminando video", str(exc))

    def upload_video_public(self, file: UploadFile) -> VideoUploadResponse:
        """
        Sube un video públicamente (sin autenticación) - Solo para desarrollo.

        Args:
            file: Archivo subido

        Returns:
            VideoUploadResponse con información del video subido

        Raises:
            VideoValidationException: Si el archivo no es válido
            MinIOStorageException: Si falla la subida a MinIO
            VideoDBException: Si falla guardar en base de datos
        """
        size_bytes = self._validate_file(file)

        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"public/{uuid4()}_{file.filename}"

        s3_client = self._get_s3_client()
        try:
            self._ensure_bucket_exists(s3_client, bucket)
            file.file.seek(0)
            extra_args = (
                {"ContentType": file.content_type} if file.content_type else None
            )
            if extra_args:
                s3_client.upload_fileobj(
                    file.file, bucket, object_key, ExtraArgs=extra_args
                )
            else:
                s3_client.upload_fileobj(file.file, bucket, object_key)
        except ClientError as exc:
            raise MinIOStorageException("Error subiendo archivo a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida", str(exc))

        # Crear registro en DB
        video = self._create_video_record(file.filename, None)

        # Actualizar storage_path
        try:
            video.storage_path = f"s3://{bucket}/{object_key}"
            self.db.commit()
        except Exception as exc:
            raise VideoDBException("Error actualizando storage_path", str(exc))

        metadata = self._extract_metadata(video.storage_path)
        self._save_metadata_to_video(video, metadata)

        return VideoUploadResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            user_id=None,
            storage_path=video.storage_path,
            uploaded_at=datetime.utcnow(),
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

        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"{user_id}/{uuid4()}_{file.filename}"

        s3_client = self._get_s3_client()
        try:
            self._ensure_bucket_exists(s3_client, bucket)
            file.file.seek(0)
            extra_args = (
                {"ContentType": file.content_type} if file.content_type else None
            )
            if extra_args:
                s3_client.upload_fileobj(
                    file.file, bucket, object_key, ExtraArgs=extra_args
                )
            else:
                s3_client.upload_fileobj(file.file, bucket, object_key)
        except ClientError as exc:
            raise MinIOStorageException("Error subiendo archivo a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida", str(exc))

        # Crear registro en DB
        video = self._create_video_record(file.filename, user_id)

        # Actualizar storage_path
        try:
            video.storage_path = f"s3://{bucket}/{object_key}"
            self.db.commit()
        except Exception as exc:
            raise VideoDBException("Error actualizando storage_path", str(exc))

        metadata = self._extract_metadata(video.storage_path)
        self._save_metadata_to_video(video, metadata)

        return VideoUploadResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            user_id=user_id,
            storage_path=video.storage_path,
            uploaded_at=datetime.utcnow(),
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

        # Extraer bucket y object_key del storage_path (formato: s3://bucket/key)
        try:
            bucket, object_key = self._extract_bucket_and_key(video.storage_path)
        except Exception as exc:
            raise BadRequestException(f"Error procesando storage_path: {str(exc)}")

        # Generar URL presignada usando endpoint público
        public_endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        public_secure = (
            settings.MINIO_SECURE
            if settings.MINIO_PUBLIC_SECURE is None
            else settings.MINIO_PUBLIC_SECURE
        )
        s3_client = self._get_s3_client(endpoint=public_endpoint, secure=public_secure)
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except ClientError as exc:
            raise MinIOStorageException("Error generando URL presignada", str(exc))

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
