FROM python:3.14-trixie AS builder

RUN pip install poetry

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root --no-interaction --no-ansi

FROM python:3.14-trixie AS runtime

RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

RUN groupadd -g 1001 appuser && \
    useradd -u 1000 -g 1001 -m -s /bin/sh appuser

WORKDIR /app
COPY ./src /app
COPY ./init-db.sh /app
COPY ./alembic.ini /app
COPY ./alembic /app/alembic

RUN chown -R appuser:appuser /app
RUN chmod +x /app/init-db.sh

USER appuser

EXPOSE 8000

WORKDIR /app
SHELL ["/bin/bash", "-c"]
CMD ["uvicorn", "secunda_assignment.main:app", "--host", "0.0.0.0", "--port", "8000"]
