FROM python:3.12-slim
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 antiword catdoc \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
RUN pip install --upgrade pip && pip install "poetry>=1.8.3" && poetry install --no-interaction --no-ansi
COPY app /app/app
ENV PYTHONPATH=/app
