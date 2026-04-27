# syntax=docker/dockerfile:1.7

# =============================================================================
# CVsAgent – multi-stage Dockerfile
#
# Targets:
#   * builder : resolves Python deps into a virtualenv
#   * base    : slim runtime with the venv + app code + non-root user (shared
#               by the CLI and the future UI)
#   * cli     : default target — runs `python main.py "$@"`
#   * ui      : placeholder for a future web UI (Streamlit / FastAPI). Built
#               via `docker compose --profile ui up` when implemented.
#
# Rebuild with: docker compose build
# =============================================================================

ARG PYTHON_VERSION=3.12
ARG APP_USER=cvsagent
ARG APP_HOME=/app

# -----------------------------------------------------------------------------
# Stage 1 — builder: install Python dependencies into an isolated virtualenv
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /build
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2 — base: shared runtime image (CLI + future UI start here)
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS base

ARG APP_USER
ARG APP_HOME

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    CVSAGENT_CV_DIR=/data/CVs \
    CVSAGENT_OUTPUT_DIR=/data/output \
    CVSAGENT_CACHE_DIR=/data/.cvsagent_cache

# Runtime OS deps: poppler + tesseract are optional (OCR). Keeping them thin
# here — users who don't need OCR can comment them out for a smaller image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      poppler-utils \
      tesseract-ocr \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system ${APP_USER} \
 && useradd --system --gid ${APP_USER} --create-home --home-dir /home/${APP_USER} ${APP_USER} \
 && mkdir -p ${APP_HOME} /data/CVs /data/output /data/.cvsagent_cache \
 && chown -R ${APP_USER}:${APP_USER} ${APP_HOME} /data

COPY --from=builder /opt/venv /opt/venv

WORKDIR ${APP_HOME}
COPY --chown=${APP_USER}:${APP_USER} . ${APP_HOME}

USER ${APP_USER}

HEALTHCHECK --interval=1m --timeout=10s --start-period=5s CMD python -c "import cvs_agent" || exit 1

LABEL org.opencontainers.image.title="CVsAgent" \
      org.opencontainers.image.description="AI-powered CV/Resume intelligence tool" \
      org.opencontainers.image.licenses="MIT"

# -----------------------------------------------------------------------------
# Stage 3 — cli: the default target, runs the batch extractor
# -----------------------------------------------------------------------------
FROM base AS cli

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]

# -----------------------------------------------------------------------------
# Stage 4 — ui: placeholder for the future web interface
#
# When the UI lands it will:
#   * install the extra dependency (e.g. streamlit / fastapi + uvicorn)
#   * expose port 8501 / 8000
#   * run the UI entrypoint
#
# For now it falls back to the CLI so `docker compose --profile ui up` does
# not fail if someone tries it early.
# -----------------------------------------------------------------------------
FROM base AS ui

EXPOSE 8501
# TODO(ui): replace with the real UI entrypoint when implemented.
CMD ["python", "main.py", "--help"]
