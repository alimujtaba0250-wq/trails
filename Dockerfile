# Dockerfile for the TrailPK web service — builds a Python 3.11 slim image

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    libcurl4-openssl-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-placeholder \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
