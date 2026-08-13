# News Aggregator Backend

FastAPI backend for the news aggregator application.

## Features

- **Multi-source scraping**: RSS feeds, Twitter/X (via Agent-Reach)
- **Background tasks**: Celery for scheduled scraping
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API**: RESTful API with automatic documentation

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- UV package manager

### Installation

1. Install dependencies with UV:

```bash
cd backend
uv pip install -r pyproject.toml
```

2. Copy environment file:

```bash
cp .env.example .env
```

3. Update `.env` with your database and Redis URLs

4. Run database migrations:

```bash
uv run alembic upgrade head
```

5. Start the API server:

```bash
uvicorn app.main:app --reload
```

6. Start Celery worker (in another terminal):

```bash
celery -A app.tasks.scrape worker --loglevel=info
```

7. Start Celery beat scheduler (in another terminal):

```bash
celery -A app.tasks.scrape beat --loglevel=info
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/news` - Get news articles (with filters)
- `GET /api/news/stats` - Get statistics
- `GET /api/news/search?q=query` - Search articles
- `GET /api/sources` - Get all sources
- `GET /api/sources/active` - Get active sources

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker

Build and run with Docker:

```bash
docker build -t news-backend .
docker run -p 8000:8000 --env-file .env news-backend
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Configuration
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── scrapers/         # Scraper implementations
│   ├── tasks/            # Celery tasks
│   └── main.py           # FastAPI application
├── Dockerfile
├── pyproject.toml        # UV configuration
└── .env.example
```
