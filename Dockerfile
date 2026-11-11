# syntax=docker/dockerfile:1.7
# Multi-stage: uv resolves and installs into /app/.venv, runtime copies the venv only.
FROM ghcr.io/astral-sh/uv:0.5.11-python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.15-slim-bookworm AS runtime
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 screener
WORKDIR /app
COPY --from=builder --chown=screener:screener /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 SCREENER_DATA_DIR=/data
VOLUME ["/data"]
USER screener
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/healthz || exit 1
# The Django project is created by TRA-34; until then the image is used for `screener` CLI runs.
CMD ["gunicorn", "--chdir", "app", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
