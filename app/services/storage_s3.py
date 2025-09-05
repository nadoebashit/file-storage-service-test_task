import io
import boto3
from botocore.client import Config
from datetime import timedelta
from app.core.config import settings

class S3Client:
    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if str(settings.MINIO_ENDPOINT).startswith("minio") else settings.S3_PUBLIC_ENDPOINT,
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.MINIO_BUCKET

    def upload_fileobj(self, key: str, fileobj):
        self._client.upload_fileobj(Fileobj=fileobj, Bucket=self.bucket, Key=key)

    def generate_presigned_url(self, key: str, expires_seconds: int = 60) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def download_to_bytes(self, key: str) -> bytes:
        buff = io.BytesIO()
        self._client.download_fileobj(self.bucket, key, buff)
        buff.seek(0)
        return buff.read()
