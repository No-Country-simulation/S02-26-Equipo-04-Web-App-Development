class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)

class InvalidCredentialsException(UnauthorizedException):
    def __init__(self):
        super().__init__("Invalid email or password")

class InactiveUserException(ForbiddenException):
    def __init__(self):
        super().__init__("User account is inactive")

class UserAlreadyExistsException(BadRequestException):
    def __init__(self):
        super().__init__("Email already registered")

class UserNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__("User not found")


# ============ VIDEO EXCEPTIONS ============

class VideoValidationException(BadRequestException):
    """Excepción para errores de validación de archivos de video"""
    def __init__(self, message: str = "Invalid video file"):
        super().__init__(message)


class MinIOStorageException(AppException):
    """Excepción para errores de almacenamiento en MinIO/S3"""
    def __init__(self, message: str = "Error storing file in MinIO", original_error: str | None = None):
        if original_error:
            message = f"{message}: {original_error}"
        super().__init__(message, status_code=500)


class VideoDBException(AppException):
    """Excepción para errores de base de datos relacionados con videos"""
    def __init__(self, message: str = "Database error", original_error: str | None = None):
        if original_error:
            message = f"{message}: {original_error}"
        super().__init__(message, status_code=500)
