# Multi-stage build for optimized image size
# Stage 1: Builder - Download pre-built wheels (no compilation needed!)
FROM python:3.11-slim AS builder

WORKDIR /app

# Install Python dependencies using pre-built wheels from PyPI
# No build tools needed - all packages have binary wheels for linux/amd64
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels --only-binary=:all: -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy wheels from builder and install (cryptography package includes libffi)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy project files
COPY . .

# Create directories, user, and set permissions in single layer
RUN mkdir -p staticfiles certificates_storage media data && \
    useradd -m -u 1000 certosaur && \
    chown -R certosaur:certosaur /app && \
    chmod 755 /app/data

# Copy and set entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown certosaur:certosaur /docker-entrypoint.sh

# Collect static files as non-root user
USER certosaur
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run the application
ENTRYPOINT ["/docker-entrypoint.sh"]
