from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60

    # Redis/S3 на Day 2
    REDIS_BROKER: str | None = None
    REDIS_BACKEND: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()
