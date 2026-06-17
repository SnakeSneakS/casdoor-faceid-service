FROM python:3.11-slim

ARG UNIFACE_EXTRA=cpu
ARG APT_MIRROR=http://mirrors.aliyun.com/debian
ARG APT_SECURITY_MIRROR=http://mirrors.aliyun.com/debian-security
ARG UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/
ARG FACEID_PRELOAD_MODE=all
ARG UNIFACE_MODEL_URL_REWRITE=

COPY --from=ghcr.io/astral-sh/uv:0.11.15 /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_DEFAULT_INDEX=${UV_DEFAULT_INDEX} \
    UV_LINK_MODE=copy \
    FACEID_HOST=0.0.0.0 \
    FACEID_PORT=8100 \
    FACEID_PRELOAD_MODE=${FACEID_PRELOAD_MODE} \
    UNIFACE_MODEL_URL_REWRITE=${UNIFACE_MODEL_URL_REWRITE} \
    UNIFACE_CACHE_DIR=/opt/uniface/models \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

RUN set -eux; \
    if [ -f /etc/apt/sources.list ]; then \
      sed -i "s|http://deb.debian.org/debian|${APT_MIRROR}|g; s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" /etc/apt/sources.list; \
    fi; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i "s|http://deb.debian.org/debian|${APT_MIRROR}|g; s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update \
    && apt-get install -y --no-install-recommends curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY casdoor_faceid_service ./casdoor_faceid_service

RUN uv sync --locked --no-dev --extra "${UNIFACE_EXTRA}" \
    && mkdir -p "${UNIFACE_CACHE_DIR}" \
    && uv run --no-sync python -m casdoor_faceid_service.preload

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/health', timeout=5)"

CMD ["python", "-m", "casdoor_faceid_service.main"]
