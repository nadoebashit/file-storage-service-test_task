from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # DB
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60

    # Redis / Celery
    REDIS_BROKER: str = "redis://redis:6379/0"
    REDIS_BACKEND: str = "redis://redis:6379/1"

    # MinIO / S3
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_BUCKET: str = "files"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    S3_PUBLIC_ENDPOINT: str = "http://minio:9000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,  # позволяем и UPPER_CASE, и lower
        extra="ignore",        # игнорировать лишние ключи вместо ошибки
    )

settings = Settings()
