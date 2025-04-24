FROM python:3.13-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

FROM base AS builder

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.8

RUN pip install "poetry==$POETRY_VERSION"

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main

FROM base AS runtime

RUN mkdir -p /config/settings /config/stateful /config/user /config/logs

RUN adduser -u 1000 --disabled-password --gecos "" python && \
    chown -R python:python /config

# non-root user
USER python

ENV DEBUG=false

COPY --from=builder /app/.venv ./.venv
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY main.py routes.py /app/

ENV PYTHONPATH=/app

EXPOSE 9705

ENTRYPOINT ["/app/.venv/bin/python3", "./main.py"]
