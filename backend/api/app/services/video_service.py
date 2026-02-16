from datetime import datetime
from uuid import UUID, uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.video import Video
from app.schemas.video import VideoUploadResponse
from app.utils.exceptions import VideoValidationException, MinIOStorageException, VideoDBException


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
        "video/webm"
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_s3_client(self):
        """Obtiene cliente S3 configurado para MinIO"""
        scheme = "https" if settings.MINIO_SECURE else "http"
        endpoint_url = f"{scheme}://{settings.MINIO_ENDPOINT}"
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
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
                    f"Error creando bucket '{bucket}'",
                    str(create_exc)
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
            raise VideoValidationException("No se pudo determinar el tamaño del archivo")
        
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
        self,
        original_filename: str,
        user_id: UUID | None
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
                status="uploaded"
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            return video
        except Exception as exc:
            self.db.rollback()
            raise VideoDBException("Error creando registro de video", str(exc))
    
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
            extra_args = {"ContentType": file.content_type} if file.content_type else None
            if extra_args:
                s3_client.upload_fileobj(file.file, bucket, object_key, ExtraArgs=extra_args)
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
        
        return VideoUploadResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            user_id=None,
            storage_path=video.storage_path,
            uploaded_at=datetime.utcnow()
        )
    
    def upload_video_authenticated(
        self,
        file: UploadFile,
        user_id: UUID
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
            extra_args = {"ContentType": file.content_type} if file.content_type else None
            if extra_args:
                s3_client.upload_fileobj(file.file, bucket, object_key, ExtraArgs=extra_args)
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
        
        return VideoUploadResponse(
            video_id=video.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            user_id=user_id,
            storage_path=video.storage_path,
            uploaded_at=datetime.utcnow()
        )
