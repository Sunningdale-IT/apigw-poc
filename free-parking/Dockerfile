# Multi-stage Dockerfile for free-parking Django app
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

RUN mkdir -p /app/staticfiles /app/media && \
    useradd -m -u 1000 freeparking && \
    chown -R freeparking:freeparking /app

RUN python manage.py collectstatic --noinput || true

USER freeparking
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "freeparking_project.wsgi:application"]
