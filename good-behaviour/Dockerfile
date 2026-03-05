# Multi-stage Dockerfile for good-behaviour Django app
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels --only-binary=:all: -r requirements.txt

FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

RUN mkdir -p /app/staticfiles /app/media /app/certs && \
    useradd -m -u 1000 goodbehaviour && \
    chown -R goodbehaviour:goodbehaviour /app

RUN python manage.py collectstatic --noinput || true

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER goodbehaviour
# 5000 = plain HTTP (health checks only), 5443 = mTLS HTTPS
EXPOSE 5000 5443

ENTRYPOINT ["/app/entrypoint.sh"]
