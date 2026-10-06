# 📰 News Aggregator

A modern, full-stack news aggregator with separate FastAPI backend and Next.js frontend. Aggregates news from multiple sources including RSS feeds, Twitter/X, and more.

## 🏗️ Architecture

The Next.js frontend reads through FastAPI. FastAPI and Celery share one
atomic, file-locked JSON datastore at `data/news.json`.

```
┌─────────────────┐       read       ┌──────────────────┐
│ Next.js :8502   │ ───────────────▶ │ FastAPI :8501    │
└─────────────────┘                  └────────┬─────────┘
                                             │ read/write
┌─────────────────┐                  ┌────────▼─────────┐
│ Celery + Redis  │ ───────────────▶ │ data/news.json  │
└─────────────────┘                  └──────────────────┘
```

## ✨ Features

### Backend (FastAPI)
- **RSS scraping**: Working out of the box - Google News, Ars Technica, The Verge
- **Background tasks**: Celery for scheduled scraping (RSS every 15 min, Twitter every 6h)
- **RESTful API**: Clean, documented API with automatic OpenAPI docs
- **Storage**: One local JSON file for articles, sources, X posts, and X replies
- **Caching**: Redis for Celery task queue

### Twitter Scraper
- **Status:** Searches a configurable X topic and stores matching posts plus their conversation threads. Built on [Agent-Reach](https://github.com/Panniantong/Agent-Reach) / `twitter-cli` with no browser dependency.
- **Auth:** required. Set `TWITTER_AUTH_TOKEN`/`TWITTER_CT0` from a logged-in x.com session (throwaway account recommended).
- **See:** [`twitter-scraper/README.md`](./twitter-scraper/README.md) for query configuration and cookie export instructions.

### Frontend (Next.js 16)
- **Backend reads**: Server Components and Route Handlers use the FastAPI JSON API
- **Backend-level caching**: FastAPI fetches are cached for 60 seconds
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

### Option 1: Docker Compose (Recommended)

Each container has its own compose file so you can start just the piece you
need - dependencies come along automatically via `include:`. See
`QUICK_START.md` for the full table.

1. **Clone and navigate**:
   ```bash
   cd news
   ```

2. **Configure X credentials** (only required for X scraping):
   ```bash
   cp backend/.env.example .env
   # Edit .env: set TWITTER_AUTH_TOKEN and TWITTER_CT0
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
   # Edit .env: Redis URL and optional X cookie credentials
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
   # Optional: create .env.local with BACKEND_URL=http://localhost:8501
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
│   │   ├── core/              # Runtime configuration
│   │   │   └── config.py      # Settings management
│   │   ├── db/
│   │   │   └── json_store.py  # Atomic JSON datastore
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
│   └── README.md
├── frontend/                   # Next.js service
│   ├── app/
│   │   ├── page.tsx           # Homepage
│   │   ├── article/[id]/      # Article detail page
│   │   ├── components/        # UI components
│   │   ├── lib/                # API client, utils
│   │   └── layout.tsx          # Root layout
│   │   ├── api/                # Route Handlers - GET /api/news, /api/twitter
│   ├── Dockerfile
│   └── package.json
├── twitter-scraper/             # Optional Agent-Reach X topic runner
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

### Frontend (Next.js, reads - Port 8502)

Backed by FastAPI (`frontend/app/lib/data.ts`) with 60-second fetch caching.

- `GET /api/news` - Get articles with filters
  - Query params: `source`, `category`, `limit`, `offset`, `hours`
- `GET /api/news/[id]` - Get a single article by id
- `GET /api/twitter` - Get scraped Twitter/X posts
  - Query params: `account`, `limit`, `offset`

### Backend (FastAPI, writes + admin - Port 8501)

- `GET /api/news` - Get articles with filters (used by scrapers/admin, not the frontend)
- `GET /api/news/stats` - Get statistics
- `GET /api/news/search?q=query` - Search articles
- `POST /api/news` - Create article (called by the RSS/Twitter scrapers)
- `GET /api/sources` - Get all sources
- `GET /api/sources/active` - Get active sources
- `GET /` - Root endpoint
- `GET /health` - Health check

**Interactive docs**: http://localhost:8501/docs

## 🐦 Twitter/X Scraping

The X task searches the runtime-configured `TWITTER_SEARCH_QUERY`, stores each
matching post, then opens its conversation and stores all fetched replies.
Agent-Reach diagnoses the current backend (`twitter-cli`), which the image
installs directly so unrelated optional-channel checks cannot break its build.

`GET /api/twitter/threads` returns each matching post grouped with its stored
conversation. Pass the exact query as `search_query` to filter by topic.

Set `TWITTER_SEARCH_QUERY` in the repo-root `.env`, for example
`TWITTER_SEARCH_QUERY='"drone delivery" lang:en -filter:retweets'`. It runs
on a timer and saves matches and threads to JSON. Requires X login cookies
(`TWITTER_AUTH_TOKEN` / `TWITTER_CT0`) since anonymous access is no longer
viable - see [`twitter-scraper/README.md`](./twitter-scraper/README.md) for
how to export them.

See [`STATUS.md`](./STATUS.md) for the history of the earlier
Playwright-based attempt and why it was replaced.

### Finding people who discuss a topic

Set `OPENAI_API_KEY` and the `TWITTER_PROFILE_*` settings in the repo-root
`.env`. The profile-analysis service deduplicates all authors found across the
topic's root posts and replies, fetches each author's latest 10-15 posts, and
uses OpenAI embeddings plus cosine similarity to retain the matching posts as
evidence. It also generates an evidence-bound structured summary of each
person's recent public posts. The default models are `text-embedding-3-large`
for matching and `gpt-6-luna` for summaries.

The people directory now includes an interactive topic search. Enter a topic
at [`/x/profiles`](http://localhost:8502/x/profiles); the backend generates an
X query plus 5-7 standalone context sentences, fetches the matching
conversations, and embeds every sentence independently. Each recent profile
post is ranked by its best cosine match across those semantic anchors.

Run it directly:

```bash
docker compose -f docker-compose.backend.yml exec backend \
  python -m app.services.twitter_profile_analysis --topic "Cheap LLM Providers"
```

Or enqueue it independently:

```bash
docker compose -f docker-compose.backend.yml exec celery-worker \
  celery -A app.tasks.scrape call analyze_twitter_profiles \
  --kwargs='{"topic":"Cheap LLM Providers"}'
```

Set `TWITTER_PROFILE_ANALYSIS_AFTER_SCRAPE=true` to trigger the same service
after every fetched topic batch. Results are available from
`GET /api/twitter/profiles` and in the filterable people directory at
[`/x/profiles`](http://localhost:8502/x/profiles).

## 📊 Data Flow

1. **Celery Beat** triggers scraping tasks (RSS every 15 min, Twitter every 6h)
2. **Celery Workers** execute scrapers (RSS, Twitter)
3. **Scrapers** fetch articles and normalize data
4. **Backend** stores everything in `data/news.json` (deduped by URL or X id)
5. **Frontend** reads articles/tweets through FastAPI
6. **Users** browse, search, and filter news

## 🚢 Deployment

### Backend Deployment Options

Mount persistent storage for `data/news.json` in any hosted environment:

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
JSON_DATA_PATH=/data/news.json
REDIS_URL=redis://...
CORS_ORIGINS=https://your-frontend.vercel.app
```

**Frontend** (Vercel):
```
BACKEND_URL=https://your-backend.example.com
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
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend shows no articles?

1. Confirm the backend is healthy: `curl http://localhost:8501/health`
2. Check that `data/news.json` exists and is writable by the backend.
3. Trigger a manual RSS scrape using the command below.

### No articles showing?

```bash
# Trigger manual scrape
docker-compose exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"

# Check celery worker logs
docker-compose logs celery-worker

# Check article count via the API
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
- **JSON** - Local development datastore
- **Redis** - Cache & task queue
- **Celery** - Distributed task queue
