# File Storage Service

REST API файлового хранилища с ролями (user/manager/admin), уровнями видимости (private/department/public), S3 (MinIO), извлечением метаданных (pdf/docx/doc) в фоне через Celery.

## Команды для запуска проекта

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.cli.seed
```

## Swagger url

http://localhost:8000/docs
