import boto3
from pathlib import Path
from uuid import UUID, uuid4
from botocore.config import Config
from botocore.exceptions import ClientError
from app.core.config import settings
from app.utils.exceptions import BadRequestException, MinIOStorageException, VideoDBException


class VideoWorkerService:

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
        )

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


    def get_video_url(self, storage_path: str, expires_in: int = 3600) -> str:
        bucket, key = storage_path.replace("s3://", "").split("/", 1)
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in
        )
    

    def get_video_public_url(self, storage_path: str, expires_in: int = 3600) -> str:
        try:
            storage_path = storage_path.replace("s3://", "")
            parts = storage_path.split("/", 1)
            if len(parts) != 2:
                raise ValueError("Formato de storage_path inválido")
            bucket, object_key = parts
        except Exception as exc:
            raise BadRequestException(f"Error procesando storage_path: {str(exc)}")
        
        # Generar URL presignada usando endpoint público
        public_endpoint = settings.MINIO_PUBLIC_ENDPOINT or settings.MINIO_ENDPOINT
        public_secure = settings.MINIO_SECURE if settings.MINIO_PUBLIC_SECURE is None else settings.MINIO_PUBLIC_SECURE
        print(f"Generando URL pública con endpoint {public_endpoint} (secure={public_secure})")
        print(f"MINIO_PUBLIC_ENDPOINT: {settings.MINIO_PUBLIC_ENDPOINT}")
        s3_client = self._get_s3_client(endpoint=public_endpoint, secure=public_secure)
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': object_key},
                ExpiresIn=expires_in
            )
        except ClientError as exc:
            raise MinIOStorageException("Error generando URL presignada", str(exc))
        return url

    def upload_local_video_to_minio(self, local_path: str, filename: str) -> str:
        """
        Sube un video local a MinIO y devuelve la ruta S3.

        Args:
            local_path: Ruta al archivo local
            filename: Nombre del archivo (ej: ejemplo.mp4)

        Returns:
            storage_path: s3://bucket/object_key

        Raises:
            MinIOStorageException: Si falla la subida
        """
        bucket = settings.MINIO_BUCKET_VIDEOS
        object_key = f"processed/{uuid4()}_{filename}"

        s3_client = self._get_s3_client()
        self._ensure_bucket_exists(s3_client, bucket)

        try:
            with open(local_path, "rb") as f:
                s3_client.upload_fileobj(f, bucket, object_key, ExtraArgs={"ContentType": "video/mp4"})
        except ClientError as exc:
            raise MinIOStorageException("Error subiendo archivo a MinIO", str(exc))
        except Exception as exc:
            raise MinIOStorageException("Error inesperado durante subida", str(exc))

        storage_path = f"s3://{bucket}/{object_key}"
        return storage_path
