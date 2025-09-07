FROM python:3.12-slim
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 antiword catdoc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
# (при наличии добавь сюда poetry.lock)
RUN pip install -U pip "poetry>=1.8.3" \
    && poetry install --no-interaction --no-ansi --no-root

COPY app /app/app
ENV PYTHONPATH=/app
