# Stage 1: Build static React + TypeScript + Vite UI
FROM node:22-alpine AS web-builder
WORKDIR /build/web

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
RUN npm run build

# Stage 2: Minimal Python 3.12 runtime (non-root)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UVICORN_WORKERS=1 \
    FORWARDED_ALLOW_IPS=127.0.0.1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && addgroup --system repoksv \
    && adduser --system --ingroup repoksv --home /home/repoksv repoksv

COPY codebase/ ./codebase/
COPY data/rubric.json ./data/rubric.json
COPY data/submissions/ ./data/submissions/
COPY eval/benchmark.csv ./eval/benchmark.csv
COPY eval/metric_spec.yaml ./eval/metric_spec.yaml
COPY deploy/smoke_check.py ./deploy/smoke_check.py
COPY run.py TEAMS.md ./
COPY --from=web-builder /build/web/dist ./web/dist

RUN mkdir -p /app/.study_logs \
    && chown -R repoksv:repoksv /app/.study_logs

USER repoksv
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "exec uvicorn codebase.server:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-1} --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-127.0.0.1}"]
