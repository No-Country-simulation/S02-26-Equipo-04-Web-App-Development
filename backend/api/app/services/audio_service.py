from uuid import UUID, uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.audio import Audio
from app.models.video import Video
from app.schemas.audio import AudioUploadResponse, AudioURLResponse
from app.services.storage_service import StorageService
from app.services.video_service import VideoService
from app.utils.exceptions import (
    AudioValidationException,
    AudioNotFoundException,
    AudioDBException,
    NotFoundException
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
    
    def __init__(self, db: Session, storage_service: StorageService, video_service: VideoService):
        self.db = db
        self.storage = storage_service
        self.video = video_service

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
        user_id: UUID | None,
        storage_path: str 
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
        if not storage_path:
            raise AudioValidationException("storage_path no puede estar vacío")
        try:
            audio = Audio(
                user_id=user_id,
                video_id=video_id,
                original_filename=original_filename,
                storage_path=storage_path,
                status="uploaded"
            )
            self.db.add(audio)
            self.db.commit()
            self.db.refresh(audio)
            return audio
        except Exception as exc:
            self.db.rollback()
            raise AudioDBException(f"Error creando registro de audio: {str(exc)}")
    
    
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
        video = self.video.get_user_video(video_id, user_id)
        if not video:
            raise NotFoundException(f"Video con ID '{video_id}' no encontrado para el usuario")
        
        # Validar archivo
        size_bytes = self._validate_file(file)
        
        storage_path, bucket, object_key = self.storage.upload_fileobj_to_minio(file.file, file.filename)
        
        
        
        # Crear registro en DB
        audio = self._create_audio_record(file.filename, video_id, user_id, storage_path)
 
        
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
            uploaded_at=audio.created_at  
        )
    
    def get_audio_url(self, audio_id: UUID, expires_in: int = 3600) -> AudioURLResponse:
        """
        Genera una URL presignada para descargar el audio.
        
        Args:
            audio_id: ID del audio
            expires_in: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            AudioURLResponse con la URL presignada
            
        Raises:
            AudioNotFoundException: Si el audio no existe
            BadRequestException: Si el audio no tiene storage_path
        """
        # Buscar el audio en la DB
        audio = self.db.query(Audio).filter(Audio.id == audio_id).first()
        if not audio:
            raise AudioNotFoundException(f"Audio con ID '{audio_id}' no encontrado")
        
        if not audio.storage_path:
            raise AudioValidationException(
                "El audio no tiene una ruta de almacenamiento válida"
            )
        
        # Generar URL presignada pública
        url = self.storage.get_video_public_url(audio.storage_path, expires_in=expires_in)
        
        return AudioURLResponse(
            audio_id=audio.id,
            url=url,
            expires_in_seconds=expires_in,
            filename=audio.original_filename
        )