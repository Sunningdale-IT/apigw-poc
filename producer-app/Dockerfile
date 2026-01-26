FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and collect static files
RUN python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput

# Create some initial data
RUN python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'producerapp.settings'); django.setup(); from producer.models import ProducedData; import random; [ProducedData.objects.create(value=random.randint(1, 100)) for _ in range(5)]"

EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "producerapp.wsgi:application"]
