"""Endpoints para publicación de videos en YouTube"""

import logging
import os
import tempfile
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.video import Video
from app.models.enums import VideoStatus
from app.services.youtube_upload_service import YouTubeUploadService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["YouTube"])


class YouTubePublishRequest(BaseModel):
    """Request body para publicar video en YouTube"""
    title: str | None = None
    description: str | None = None
    privacy: str = "private"  # "public", "private", "unlisted"


@router.post("/publish/{job_id}", response_model=Dict[str, Any])
async def publish_video_to_youtube(
    job_id: str,
    request: YouTubePublishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Publica un video procesado en YouTube.
    
    El usuario debe haber conectado su cuenta de YouTube previamente
    mediante Google OAuth (GET /api/v1/auth/google/authorize).
    
    Args:
        job_id: UUID del job (video procesado) en nuestra base de datos
        request: Configuración de publicación (título, descripción, privacidad)
        current_user: Usuario autenticado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)
    
    Returns:
        Información del video publicado en YouTube (ID, URL, etc.)
    
    Raises:
        400: Usuario no tiene cuenta de YouTube conectada
        403: Job no pertenece al usuario
        404: Job no encontrado
        500: Error al subir a YouTube
    """
    logger.info(f"📤 Solicitud de publicación en YouTube - job_id={job_id}, user_id={current_user.id}")
    from app.models.job import Job
    from app.models.enums import JobStatus
    
    # 1. Buscar el job en la base de datos
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_id debe ser un UUID válido"
        )
    
    job = db.query(Job).filter(Job.id == job_uuid).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} no encontrado"
        )
    
    # 2. Verificar que el job pertenece al usuario actual
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para publicar este video"
        )
    
    # 3. Verificar que el job está listo para publicar (completado)
    if job.status != JobStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El procesamiento del video aún no está listo. Estado actual: {job.status}"
        )
    
    if not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El job no tiene ruta de almacenamiento de salida"
        )
    
    # 4. Descargar video de MinIO a archivo temporal
    temp_file = None
    try:
        storage_service = StorageService()
        
        logger.info(f"📥 Descargando video de MinIO: {job.output_path}")
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Obtener el video al que pertenece el job para el título (Fallback)
        video = db.query(Video).filter(Video.id == job.video_id).first()
        
        # Obtener bucket y key de la ruta s3://
        try:
            # Si job.output_path es una URL normal o s3
            if "localhost:9000/" in job.output_path:
                # Extraer de URL pública
                # http://localhost:9000/videos/processed/...
                parts = job.output_path.split("localhost:9000/")[1].split("?")[0].split("/", 1)
                bucket_name = parts[0]
                object_name = parts[1]
            else:
                bucket_name, object_name = storage_service._extract_bucket_and_key(job.output_path)
        except Exception:
            # Fallback a asunciones por defecto
            bucket_name = settings.MINIO_BUCKET_VIDEOS
            # Limpiar posible ruta de dominio local
            object_name = job.output_path.split("?")[-1] if "?" in job.output_path else job.output_path
            if object_name.startswith("http"):
                object_name = object_name.split("/", 4)[-1].split("?")[0]
        
        # Usar boto3 client de la forma correcta
        storage_service.client.download_file(
            Bucket=bucket_name,
            Key=object_name,
            Filename=temp_file_path
        )
        
        logger.info(f"✅ Video descargado a: {temp_file_path}")
        
        # 5. Preparar metadata del video
        original_title = video.original_filename if video else f"Clip {job_id[:8]}"
        title = request.title or f"Clip de {original_title}"
        description = request.description or "Video generado con NoCountry Video Processor"
        privacy = request.privacy
        
        # Tags básicos
        tags = ["nocountry", "ai", "shorts"]
        
        # 6. Subir a YouTube
        youtube_service = YouTubeUploadService(db)
        
        result = await youtube_service.upload_video(
            user_id=str(current_user.id),
            video_file_path=temp_file_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
        )
        
        logger.info(f"✅ Video publicado en YouTube: {result['video_url']}")
        
        # 7. (Opcional) Actualizar estado del video en BD
        # video.status = VideoStatus.PUBLISHED
        # db.commit()
        
        return {
            "success": True,
            "message": "Video publicado en YouTube exitosamente",
            "job_id": str(job.id),
            "youtube_video_id": result["video_id"],
            "youtube_url": result["video_url"],
            "title": result["title"],
            "privacy": result["privacy_status"],
            "thumbnail_url": result.get("thumbnail_url"),
        }
    
    except HTTPException:
        raise  # Re-lanzar HTTPExceptions
    except Exception as e:
        logger.error(f"❌ Error inesperado publicando video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
    finally:
        # 8. Limpiar archivo temporal
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"🗑️ Archivo temporal eliminado: {temp_file_path}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar archivo temporal: {e}")


@router.get("/status")
async def check_youtube_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verifica si el usuario tiene una cuenta de YouTube conectada.
    
    Útil para que el frontend sepa si debe mostrar el botón de
    "Conectar YouTube" o "Publicar en YouTube".
    
    Returns:
        Estado de la conexión de YouTube del usuario
    """
    from app.models.oauth_token import OAuthToken
    
    oauth_token = (
        db.query(OAuthToken)
        .filter(
            OAuthToken.user_id == current_user.id,
            OAuthToken.provider == "youtube"
        )
        .first()
    )
    
    if not oauth_token:
        return {
            "connected": False,
            "message": "Usuario no tiene cuenta de YouTube conectada"
        }
    
    return {
        "connected": True,
        "provider_username": oauth_token.provider_username,
        "provider_user_id": oauth_token.provider_user_id,
        "token_expires_at": oauth_token.expires_at.isoformat() if oauth_token.expires_at else None,
        "is_expired": oauth_token.is_expired(),
    }
