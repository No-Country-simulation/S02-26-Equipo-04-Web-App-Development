from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import secrets

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, env_file_encoding="utf-8")
    
    APP_NAME: str = "NoCountry Video API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    DATABASE_URL: str = Field(...)
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_ECHO: bool = Field(default=False)
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL debe comenzar con postgresql://")
        return v
    
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)
    
    MINIO_ENDPOINT: str = Field(default="minio:9000")
    MINIO_ACCESS_KEY: str = Field(default="minio")
    MINIO_SECRET_KEY: str = Field(default="miniopass")
    MINIO_BUCKET_VIDEOS: str = Field(default="videos")
    MINIO_SECURE: bool = Field(default=False)
    # Endpoint público para URLs presignadas (accesible desde navegador)
    MINIO_PUBLIC_ENDPOINT: str | None = Field(default=None)
    MINIO_PUBLIC_SECURE: bool | None = Field(default=None)
    
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v, info):
        if info.data.get("ENVIRONMENT") == "production" and len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres en producción")
        return v
    
    # === GOOGLE OAUTH ===
    GOOGLE_CLIENT_ID: str = Field(...)
    GOOGLE_CLIENT_SECRET: str = Field(...)
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:3000/auth/callback")
    
    @field_validator("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    @classmethod
    def validate_google_credentials(cls, v, info):
        if info.data.get("ENVIRONMENT") == "production" and not v:
            raise ValueError(f"{info.field_name} is required in production")
        return v
    
    ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    RATE_LIMIT_ENABLED: bool = Field(default=False)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

settings = Settings()
