# TrailPK

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.15-red?logo=django)
![Scrapy](https://img.shields.io/badge/Scrapy-2.11-darkgreen?logo=scrapy)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)

A Django REST Framework + Scrapy platform for discovering and managing hiking trails in Pakistan.

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Backend     | Django 4.2, Django REST Framework |
| Scraping    | Scrapy 2.11                       |
| Database    | PostgreSQL 16                     |
| Config      | python-decouple                   |
| Dev Tools   | django-debug-toolbar              |
| Production  | Gunicorn, WhiteNoise              |
| Containers  | Docker, Docker Compose            |

---

## Quick Start

> **Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone <repo-url>
cd trailpk

# 2. Set up environment variables
cp .env.example .env
# Edit .env and fill in the required values

# 3. Build and start all services
docker compose up --build

# 4. Run migrations (in a separate terminal)
docker compose exec web python manage.py migrate

# 5. Create a superuser
docker compose exec web python manage.py createsuperuser

# 6. Visit the app
# API:   http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

---

## Project Structure

```
trailpk/
├── config/          # Django settings (base / local / production)
├── apps/
│   ├── trails/      # Main trails app (models, serializers, views)
│   └── core/        # Shared utilities
├── scraper/         # Scrapy project
├── requirements/    # Layered pip requirements
├── Dockerfile
├── docker-compose.yml
└── manage.py
```
