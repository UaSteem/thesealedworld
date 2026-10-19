# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e

### Stage 1: builder
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS builder
WORKDIR /build

RUN pip install --no-cache-dir uv==0.11.8

COPY pyproject.toml uv.lock ./
RUN uv export --no-dev --group tg-bot --no-emit-project --no-sources --format requirements-txt -o requirements.txt

RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

### Stage 2: runtime
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS runtime
WORKDIR /app

RUN adduser --disabled-password --uid 1000 appuser

COPY --from=builder /venv /venv

ENV PATH="/venv/bin:$PATH" \
    PYTHONPATH="/app:/app/src" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY src/tg_bot ./src/tg_bot
COPY src/shared ./src/shared

RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "tg_bot.launcher"]
