ARG PYTHON_BASE_IMAGE=python:3.12-slim
FROM ${PYTHON_BASE_IMAGE}

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV NO_PROXY=${NO_PROXY}
ENV PYTHONUNBUFFERED=1
ENV APP_WORK_DIR=/app/data

WORKDIR /app

ARG APT_MIRROR=
RUN set -eux; \
  if [ -n "$APT_MIRROR" ]; then \
    sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    sed -i "s|security.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources || true; \
  fi; \
  apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30; \
  (apt-get install -y --no-install-recommends ffmpeg gcc python3-dev || \
   (apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=30 && \
    apt-get install -y --fix-missing --no-install-recommends ffmpeg gcc python3-dev)); \
  rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
ARG PIP_INDEX_URL=
RUN if [ -n "$PIP_INDEX_URL" ]; then \
    pip install --no-cache-dir -r requirements.txt -i "$PIP_INDEX_URL"; \
  else \
    pip install --no-cache-dir -r requirements.txt; \
  fi

COPY . .

RUN mkdir -p /app/data/assets /app/logs

VOLUME ["/app/data", "/app/logs"]

EXPOSE 11451

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "11451"]
