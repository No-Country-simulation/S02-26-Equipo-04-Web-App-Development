"""
Enums para los modelos de la aplicación.
Definidos centralmente para reutilización en modelos, schemas y servicios.
"""
import enum


class UserRole(str, enum.Enum):
    """
    Roles de usuario en el sistema.
    
    - USER: Usuario regular con permisos básicos
    - ADMIN: Administrador con permisos elevados
    """
    USER = "USER"
    ADMIN = "ADMIN"


class VideoStatus(str, enum.Enum):
    """
    Estados posibles de un video en el sistema.
    """
    PENDING_METADATA = "pending_metadata"
    PROCESSING_METADATA = "processing_metadata"
    AVAILABLE = "available"
    INVALID = "invalid"


class JobType(str, enum.Enum):
    """
    Tipos de trabajos que se pueden procesar.
    
    - REFRAME: Reencuadre de video
     ... a futuro THUMBNAIL, TRANSCRIPTION, etc.
    """ 
    REFRAME = "REFRAME"
    AUTO_REFRAME = "AUTO_REFRAME"
    ADD_AUDIO = "ADD_AUDIO"


class JobStatus(str, enum.Enum):
    """
    Estados posibles de un trabajo en el sistema.
    PENDING = creado, requiere una confirmacion del sistema/envio a redis...
    QUEUED = en cola para ser procesado....(redis ya lo recibio)
    RUNNING = siendo procesado
    DONE = terminado exitosamente
    FAILED = fallido durante el procesamiento
    CANCELLED = cancelado por el usuario
    RETRYING = reinicado el procesamiento
     ... (a futuro: CANCELLED, RETRYING, QUEUED)
    """
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"