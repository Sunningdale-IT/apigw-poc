# Multi-stage build for optimized image size
# Stage 1: Builder - Download pre-built wheels (no compilation needed!)
FROM python:3.11-slim AS builder

WORKDIR /app

# Install Python dependencies using pre-built wheels from PyPI
# psycopg2-binary includes pre-compiled PostgreSQL bindings
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels --only-binary=:all: -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy wheels from builder and install (psycopg2-binary includes libpq)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Create directories and non-root user in single layer
RUN mkdir -p /app/static/uploads /app/staticfiles && \
    useradd -m -u 1000 dogcatcher && \
    chown -R dogcatcher:dogcatcher /app

# Collect static files as non-root user
USER dogcatcher
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=dogcatcher_project.settings

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn dogcatcher_project.wsgi:application --bind 0.0.0.0:5000 --workers 2 --threads 2"]
