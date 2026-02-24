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
from app.models.audio import Audio
from app.models.video import Video
from app.schemas.audio import AudioUploadResponse
from app.utils.exceptions import (
    AudioValidationException,
    AudioNotFoundException,
    MinIOStorageException,
    NotFoundException,
    AppException,
)


class AudioService:
    """Servicio de audios - Maneja validación, almacenamiento y metadata de audios"""
    
    # Configuración de validación
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {"mp3", "wav", "aac", "flac", "ogg", "m4a", "wma", "opus"}
    ALLOWED_MIME_TYPES = {
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/aac",
        "audio/flac",
        "audio/ogg",
        "audio/mp4",
        "audio/x-m4a",
        "audio/x-ms-wma",
        "audio/opus"
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
        Valida el archivo de audio subido.
        
        Args:
            file: Archivo subido
            
        Returns:
            Tamaño del archivo en bytes
            
        Raises:
            AudioValidationException: Si el archivo no cumple los requisitos
        """
        # Validar nombre
        if not file.filename:
            raise AudioValidationException("El archivo debe tener un nombre")
        
        # Validar extensión
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise AudioValidationException(
                f"Extensión no permitida. Extensiones válidas: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
            )
        
        # Validar MIME type
        if file.content_type:
            if file.content_type not in self.ALLOWED_MIME_TYPES:
                raise AudioValidationException(
                    f"Tipo de archivo no válido. MIME type: {file.content_type}"
                )
        
        # Obtener tamaño
        try:
            file.file.seek(0, 2)
            size_bytes = file.file.tell()
            file.file.seek(0)
        except Exception:
            raise AudioValidationException("No se pudo determinar el tamaño del archivo")
        
        # Validar tamaño no vacío
        if size_bytes == 0:
            raise AudioValidationException("El archivo está vacío")
        
        # Validar tamaño máximo
        if size_bytes > self.MAX_FILE_SIZE_BYTES:
            max_mb = self.MAX_FILE_SIZE_BYTES / (1024 * 1024)
            raise AudioValidationException(
                f"El archivo excede el tamaño máximo permitido ({max_mb}MB)"
            )
        
        return size_bytes
    
    def _create_audio_record(
        self,
        original_filename: str,
        video_id: UUID,
        user_id: UUID | None
    ) -> Audio:
        """
        Crea un registro de audio en la base de datos.
        
        Args:
            original_filename: Nombre original del archivo
            video_id: ID del video asociado
            user_id: ID del usuario autenticado
            
        Returns:
            Audio creado
            
        Raises:
            AppException: Si falla la creación del registro
        """
        try:
            audio = Audio(
                user_id=user_id,
                video_id=video_id,
                original_filename=original_filename,
                storage_path=None,
                status="uploaded"
            )
            self.db.add(audio)
            self.db.commit()
            self.db.refresh(audio)
            return audio
        except Exception as exc:
            self.db.rollback()
            raise AppException(f"Error creando registro de audio: {str(exc)}", status_code=500)
    
    def _extract_audio_metadata(self, storage_path: str) -> dict:
        """
        Extrae metadata del audio en MinIO usando ffprobe.
        
        Args:
            storage_path: Ruta del audio en formato s3://bucket/key
            
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
            print(f"Error extrayendo metadata de audio: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _save_metadata_to_audio(self, audio: Audio, metadata: dict) -> None:
        """
        Actualiza el registro del audio con metadata extraída.
        
        Args:
            audio: Objeto Audio a actualizar
            metadata: Dict con metadata extraída por ffprobe
        """
        try:
            if metadata.get("format"):
                audio.duration_seconds = int(float(metadata["format"].get("duration", 0)))
                audio.bitrate = int(metadata["format"].get("bit_rate", 0))
            
            for stream in metadata.get("streams", []):
                if stream["codec_type"] == "audio":
                    audio.sample_rate = stream.get("sample_rate")
                    audio.channels = stream.get("channels")
                    audio.codec = stream.get("codec_name")
            
            self.db.commit()
        except Exception as e:
            print(f"Error guardando metadata de audio: {e}")
            self.db.rollback()
    
    def upload_audio_to_video(
        self,
        file: UploadFile,
        video_id: UUID,
        user_id: UUID
    ) -> AudioUploadResponse:
        """
        Sube un audio asociado a un video.
        
        Args:
            file: Archivo de audio subido
            video_id: ID del video al que pertenece el audio
            user_id: ID del usuario autenticado
            
        Returns:
            AudioUploadResponse con información del audio subido
            
        Raises:
            NotFoundException: Si el video no existe
            AudioValidationException: Si el archivo no es válido
            MinIOStorageException: Si falla la subida a MinIO
            AppException: Si falla guardar en base de datos
        """
        # Verificar que el video existe
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise NotFoundException(f"Video con ID {video_id} no encontrado")
        
        # Validar archivo
        size_bytes = self._validate_file(file)
        
        # Configurar bucket y object_key
        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"{user_id}/audios/{video_id}/{uuid4()}_{file.filename}"
        
        # Subir a MinIO
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
            raise MinIOStorageException("Error subiendo archivo de audio a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida de audio", str(exc))
        
        # Crear registro en DB
        audio = self._create_audio_record(file.filename, video_id, user_id)
        
        # Actualizar storage_path
        try:
            audio.storage_path = f"s3://{bucket}/{object_key}"
            self.db.commit()
        except Exception as exc:
            raise AppException(f"Error actualizando storage_path del audio: {str(exc)}", status_code=500)
        
        # Extraer y guardar metadata
        metadata = self._extract_audio_metadata(audio.storage_path)
        self._save_metadata_to_audio(audio, metadata)
        
        return AudioUploadResponse(
            audio_id=audio.id,
            bucket=bucket,
            object_key=object_key,
            filename=file.filename,
            content_type=file.content_type,
            size_bytes=size_bytes,
            video_id=video_id,
            user_id=user_id,
            storage_path=audio.storage_path,
            uploaded_at=datetime.utcnow()
        )
