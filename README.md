# 📰 News Aggregator

A modern, full-stack news aggregator with separate FastAPI backend and Next.js frontend. Aggregates news from multiple sources including RSS feeds, Twitter/X, and more.

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Next.js       │  HTTP   │   FastAPI        │
│   Frontend      │ ──────> │   Backend        │
│   (Port 8502)   │         │   (Port 8501)    │
└─────────────────┘         └──────────────────┘
                                     │
                            ┌────────┼────────┐
                            │        │        │
                       ┌────▼────┐  │  ┌─────▼────────┐
                       │ Supabase │  │  │   Redis      │
                       │(Postgres)│  │  │  (Port 8500) │
                       └──────────┘  │  └──────────────┘
                                     │
                                ┌────▼────┐
                                │ Celery  │
                                │ Workers │
                                │ + Beat  │
                                └─────────┘
```

## ✨ Features

### Backend (FastAPI)
- **RSS scraping**: Working out of the box - Google News, Ars Technica, The Verge
- **Background tasks**: Celery for scheduled scraping (RSS every 15 min, Twitter every 6h)
- **RESTful API**: Clean, documented API with automatic OpenAPI docs
- **Database**: Supabase (Postgres via SQLAlchemy for RSS, Supabase REST API for Twitter) - no local Postgres
- **Caching**: Redis for Celery task queue

### Twitter Scraper
- **Status:** ✅ Given a list of X/Twitter profile URLs, fetches each profile's most recent posts. Built directly on [Agent-Reach](https://github.com/Panniantong/Agent-Reach), which provisions and health-checks the Twitter backend (currently `twitter-cli`) - no browser/Chromium.
- **Auth:** required. Set `TWITTER_AUTH_TOKEN`/`TWITTER_CT0` from a logged-in x.com session (throwaway account recommended).
- **See:** [`twitter-scraper/README.md`](./twitter-scraper/README.md) for setup, profile URL config, and cookie export instructions.

### Frontend (Next.js 16)
- **Server Components**: Fast, SEO-friendly pages
- **Modern UI**: Tailwind CSS with dark mode support
- **Real-time updates**: Auto-refresh with Next.js revalidation
- **Search**: Full-text search across articles
- **Filtering**: Filter by source, category, and time range
- **Statistics**: Dashboard with aggregated stats

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OR: Python 3.12+, Node.js 20+, Redis
- A [Supabase](https://supabase.com) project (free tier is fine) - the only database, no local Postgres

### Option 1: Docker Compose (Recommended)

Each container has its own compose file so you can start just the piece you
need - dependencies come along automatically via `include:`. See
`QUICK_START.md` for the full table.

1. **Clone and navigate**:
   ```bash
   cd news
   ```

2. **Configure Supabase** (required):
   ```bash
   cp backend/.env.example .env
   # Edit .env: set DATABASE_URL, SUPABASE_URL, SUPABASE_KEY
   # See backend/README.md > Twitter/X scraping (Supabase) for how to get these
   ```

3. **Start everything**:
   ```bash
   docker compose up --build
   ```

   Or start just one part of the stack, and its dependencies come with it:
   ```bash
   docker compose -f docker-compose.backend.yml up -d --build   # redis + backend + celery
   docker compose -f docker-compose.frontend.yml up -d --build  # + frontend
   docker compose -f docker-compose.redis.yml up -d             # just redis
   ```

4. **Access the application**:
   - Frontend: http://localhost:8502
   - Backend API: http://localhost:8501
   - API Docs: http://localhost:8501/docs

5. **Initial data**:
   The RSS scraper will automatically start fetching articles every 15 minutes. You can trigger it manually:
   ```bash
   docker compose -f docker-compose.backend.yml exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"
   ```

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend**:
   ```bash
   cd backend
   ```

2. **Install UV** (if not installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r pyproject.toml
   ```

4. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env: DATABASE_URL (Supabase Postgres connection string),
   # SUPABASE_URL, SUPABASE_KEY, and Redis URL
   ```

5. **Start services** (separate terminals):
   ```bash
   # Terminal 1: API Server
   uvicorn app.main:app --reload

   # Terminal 2: Celery Worker
   celery -A app.tasks.scrape worker --loglevel=info

   # Terminal 3: Celery Beat
   celery -A app.tasks.scrape beat --loglevel=info
   ```

#### Frontend Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with backend URL (http://localhost:8501)
   ```

4. **Start dev server**:
   ```bash
   npm run dev
   ```

5. **Access**: http://localhost:3000

## 📁 Project Structure

```
news/
├── backend/                    # FastAPI service
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── news.py        # News endpoints
│   │   │   └── sources.py     # Sources endpoints
│   │   ├── core/              # Configuration + constants (TWITTER_ACCOUNTS)
│   │   │   └── config.py      # Settings management
│   │   ├── db/                # Database setup (SQLAlchemy session + Supabase client)
│   │   │   └── session.py     # SQLAlchemy session (Supabase Postgres)
│   │   ├── models/            # Database models
│   │   │   └── article.py     # Article & Source models
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── article.py     # API schemas
│   │   ├── scrapers/          # Scraper implementations
│   │   │   ├── base.py        # Base scraper class
│   │   │   ├── rss.py         # RSS feed scraper
│   │   │   └── twitter.py     # Twitter scraper (twitter-cli)
│   │   ├── tasks/             # Background tasks
│   │   │   └── scrape.py      # Celery tasks
│   │   └── main.py            # FastAPI app entry
│   ├── Dockerfile
│   ├── pyproject.toml         # UV dependencies
│   ├── supabase_schema.sql    # Twitter posts table DDL
│   └── README.md
├── frontend/                   # Next.js service
│   ├── app/
│   │   ├── page.tsx           # Homepage
│   │   ├── article/[id]/      # Article detail page
│   │   ├── components/        # UI components
│   │   ├── lib/                # API client, utils
│   │   └── layout.tsx          # Root layout
│   ├── Dockerfile
│   └── package.json
├── twitter-scraper/             # Agent-Reach based Twitter/X profile scraper
│   ├── Dockerfile
│   └── scraper.py
├── docker-compose.redis.yml            # Redis, standalone
├── docker-compose.backend.yml          # Backend + Celery (includes redis)
├── docker-compose.frontend.yml         # Frontend (includes backend stack)
├── docker-compose.twitter-scraper.yml  # Scraper (includes backend stack)
├── docker-compose.yml                  # Full stack (includes everything above)
├── CONTAINERS.md                       # Exact command to run each container
└── README.md                           # This file
```

## 🔌 API Endpoints

### News

- `GET /api/news` - Get articles with filters
  - Query params: `source`, `category`, `limit`, `offset`, `hours`
- `GET /api/news/stats` - Get statistics
- `GET /api/news/search?q=query` - Search articles
- `POST /api/news` - Create article (internal use)

### Sources

- `GET /api/sources` - Get all sources
- `GET /api/sources/active` - Get active sources

### System

- `GET /` - Root endpoint
- `GET /health` - Health check

**Interactive docs**: http://localhost:8501/docs

## 🐦 Twitter/X Scraping

**Status:** ✅ Operational, given profile URLs to follow. Built directly on [Agent-Reach](https://github.com/Panniantong/Agent-Reach) (installed from its GitHub source), which provisions and health-checks the Twitter backend - no browser dependency, so no ARM64/Playwright issues.

Give it a comma-separated list of profile URLs via `TWITTER_PROFILE_URLS` in
`docker-compose.twitter-scraper.yml`; it fetches each profile's most recent
posts on a timer and saves them to the backend. Requires X login cookies
(`TWITTER_AUTH_TOKEN` / `TWITTER_CT0`) since anonymous access is no longer
viable - see [`twitter-scraper/README.md`](./twitter-scraper/README.md) for
how to export them.

See [`STATUS.md`](./STATUS.md) for the history of the earlier
Playwright-based attempt and why it was replaced.

## 📊 Data Flow

1. **Celery Beat** triggers scraping tasks (RSS every 15 min, Twitter every 6h)
2. **Celery Workers** execute scrapers (RSS, Twitter)
3. **Scrapers** fetch articles and normalize data
4. **Backend** stores RSS articles in Supabase Postgres (SQLAlchemy, deduped by URL) and Twitter posts via the Supabase REST API (deduped by `tweet_id`)
5. **Frontend** fetches articles via REST API
6. **Users** browse, search, and filter news

## 🚢 Deployment

### Backend Deployment Options

Database is already Supabase (works the same in any hosting environment):

- **Railway**: Push backend to Railway
- **Render**: Deploy as Web Service
- **DigitalOcean**: Use App Platform or Droplet
- **Fly.io**: Deploy the backend container

### Frontend Deployment

- **Vercel** (recommended): `vercel --prod` from frontend/
- **Netlify**: Connect GitHub repo
- **Cloudflare Pages**: Static site deployment

### Environment Variables

**Backend** (Railway/Render):
```
DATABASE_URL=postgresql://postgres:...@db.your-project.supabase.co:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
REDIS_URL=redis://...
CORS_ORIGINS=https://your-frontend.vercel.app
```

**Frontend** (Vercel):
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

## 🛠️ Development

### Backend Development

```bash
# Format code
black app/

# Type check
mypy app/

# Run tests
pytest
```

### Frontend Development

```bash
# Lint
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

## 🐛 Troubleshooting

### Backend not starting?

```bash
# Check backend logs (auth/connection errors to Supabase show up here)
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend can't connect to backend?

1. Check `NEXT_PUBLIC_API_URL` in `.env.local`
2. Verify backend is running: `curl http://localhost:8501/health`
3. Check CORS settings in `backend/app/core/config.py`

### No articles showing?

```bash
# Trigger manual scrape
docker-compose exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"

# Check celery worker logs
docker-compose logs celery-worker

# Check article count via the API instead of psql (no local Postgres)
curl http://localhost:8501/api/news/stats
```

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome! Please ensure:

1. Code is formatted (black for Python, prettier for TypeScript)
2. Tests pass
3. Documentation is updated

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework
- **Agent-Reach** - Multi-platform scraping tool
- **Tailwind CSS** - Utility-first CSS
- **Supabase** - Database (Postgres) & Twitter post storage
- **Redis** - Cache & task queue
- **Celery** - Distributed task queue
