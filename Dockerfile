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
RUN chmod -R 755 /config

# Set environment variables
ENV PYTHONPATH=/app
# ENV APP_TYPE=sonarr # APP_TYPE is likely managed via config now, remove if not needed

# Expose port
EXPOSE 9705

# Run the main application using the new entry point
CMD ["python3", "main.py"]