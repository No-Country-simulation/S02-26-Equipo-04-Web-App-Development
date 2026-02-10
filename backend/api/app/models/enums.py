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
