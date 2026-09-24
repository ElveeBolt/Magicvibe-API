ARG PYTHON_IMAGE=python:3.14.6-alpine3.24
ARG APP_USER=magicvibe
ARG APP_GROUP=magicvibe
ARG APP_DIR=/home/${APP_USER}/app

# Stage 1: Builder
FROM ${PYTHON_IMAGE} AS builder

ARG APP_DIR

COPY --from=ghcr.io/astral-sh/uv:0.12.4 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR ${APP_DIR}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Stage 2: Final
FROM ${PYTHON_IMAGE}

ARG APP_USER
ARG APP_GROUP
ARG APP_DIR

RUN addgroup -S ${APP_GROUP} && adduser -S ${APP_USER} -G ${APP_GROUP}

ENV PATH="${APP_DIR}/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR ${APP_DIR}

COPY --from=builder ${APP_DIR}/.venv ${APP_DIR}/.venv
COPY alembic.ini .
COPY alembic ./alembic

USER ${APP_USER}

EXPOSE 8000

CMD ["uvicorn", "magicvibe.main:app", "--host", "0.0.0.0", "--port", "8000"]
