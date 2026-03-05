FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels --only-binary=:all: -r requirements.txt

FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Create necessary directories and user
RUN mkdir -p /app/staticfiles /app/media && \
    useradd -m -u 1000 moviezzz && \
    chown -R moviezzz:moviezzz /app

# Collect static files
RUN python manage.py collectstatic --noinput || true

USER moviezzz

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "60", "moviezzz_project.wsgi:application"]
