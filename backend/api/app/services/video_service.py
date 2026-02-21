from datetime import datetime
from uuid import UUID, uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
import boto3
import subprocess
import json
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.video import Video
from app.schemas.video import VideoUploadResponse, VideoURLResponse
from app.utils.exceptions import (
    BadRequestException,
    MinIOStorageException,
    NotFoundException,
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
        "video/webm"
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
        user_id: UUID
    ) -> Video:
        """
        Crea un registro de video en la base de datos.
        
        Args:
            original_filename: Nombre original del archivo
            user_id: ID del usuario autenticado
            
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
    
    def _extract_metadata(self, storage_path: str) -> dict:
        """
        Extrae metadata del video en MinIO usando ffprobe.
        
        Args:
            storage_path: Ruta del video en formato s3://bucket/key
            
        Returns:
            Dict con la metadata extraída (vacío si falla)
        """
        try:
            # Extraer bucket y object_key del storage_path
            storage_path_clean = storage_path.replace("s3://", "")
            parts = storage_path_clean.split("/", 1)
            if len(parts) != 2:
                print(f"Formato de storage_path inválido: {storage_path}")
                return {}
            
            bucket, object_key = parts
            
            # Generar URL presignada para que ffprobe pueda acceder
            s3_client = self._get_s3_client()
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=3600
            )
            
            # Usar ffprobe con la URL presignada
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                presigned_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"ffprobe error: {result.stderr}")
                return {}
            return json.loads(result.stdout) if result.stdout else {}
        except Exception as e:
            print(f"Error extrayendo metadata: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _save_metadata_to_video(self, video: Video, metadata: dict) -> None:
        """
        Actualiza el registro del video con metadata extraída.
        
        Args:
            video: Objeto Video a actualizar
            metadata: Dict con metadata extraída por ffprobe
        """
        try:
            if metadata.get("format"):
                video.duration_seconds = int(float(metadata["format"].get("duration", 0)))
            
            for stream in metadata.get("streams", []):
                if stream["codec_type"] == "video":
                    fps_str = stream.get("r_frame_rate", "0")
                    if fps_str and "/" in str(fps_str):
                        fps_value = float(fps_str.split("/")[0])
                        video.fps = int(fps_value)
                    video.width = stream.get("width")
                    video.height = stream.get("height")
                    video.codec = stream.get("codec_name")
                    video.bitrate = stream.get("bit_rate")
                elif stream["codec_type"] == "audio":
                    video.has_audio = True
                    video.audio_codec = stream.get("codec_name")
            
            self.db.commit()
        except Exception as e:
            print(f"Error guardando metadata: {e}")
            self.db.rollback()
    
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
        
        # Extraer y guardar metadata
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
            uploaded_at=datetime.utcnow()
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
            raise BadRequestException("El video no tiene una ruta de almacenamiento válida")
        
        # Extraer bucket y object_key del storage_path (formato: s3://bucket/key)
        try:
            storage_path = video.storage_path.replace("s3://", "")
            parts = storage_path.split("/", 1)
            if len(parts) != 2:
                raise ValueError("Formato de storage_path inválido")
            bucket, object_key = parts
        except Exception as exc:
            raise BadRequestException(f"Error procesando storage_path: {str(exc)}")
        
        # Generar URL presignada usando endpoint público
        public_endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        public_secure = settings.MINIO_SECURE if settings.MINIO_PUBLIC_SECURE is None else settings.MINIO_PUBLIC_SECURE
        s3_client = self._get_s3_client(endpoint=public_endpoint, secure=public_secure)
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expires_in
            )
        except ClientError as exc:
            raise MinIOStorageException("Error generando URL presignada", str(exc))
        
        return VideoURLResponse(
            video_id=video.id,
            url=url,
            expires_in_seconds=expires_in,
            filename=video.original_filename
        )
