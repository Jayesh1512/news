# 📰 News Aggregator

A modern, full-stack news aggregator with separate FastAPI backend and Next.js frontend. Aggregates news from multiple sources including RSS feeds, Twitter/X, and more.

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Next.js       │  HTTP   │   FastAPI        │
│   Frontend      │ ──────> │   Backend        │
│   (Port 3000)   │         │   (Port 8000)    │
└─────────────────┘         └──────────────────┘
                                     │
                            ┌────────┼────────┐
                            │        │        │
                       ┌────▼────┐  │  ┌─────▼────────┐
                       │PostgreSQL│  │  │   Twitter    │
                       │Database  │  │  │   Scraper    │
                       └──────────┘  │  │ (Playwright) │
                                     │  └──────────────┘
                                ┌────▼────┐
                                │  Redis  │
                                │         │
                                └─────────┘
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
- **Background tasks**: Celery for scheduled scraping every 15 minutes
- **RESTful API**: Clean, documented API with automatic OpenAPI docs
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for Celery task queue

### Twitter Scraper
- **Status:** ❌ Not operational (Docker build fails)
- **Code written:** scraper.py complete but cannot be containerized
- **Recommendation:** Use official Twitter API instead of web scraping
- **See:** `twitter-scraper/STATUS.md` for details and alternatives

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
- OR: Python 3.12+, Node.js 20+, PostgreSQL, Redis

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate**:
   ```bash
   cd news
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Initial data**:
   The RSS scraper will automatically start fetching articles every 15 minutes. You can trigger it manually:
   ```bash
   docker-compose exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"
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
   # Edit .env with your database and Redis URLs
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
   # Edit .env.local with backend URL (http://localhost:8000)
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
│   │   ├── core/              # Configuration
│   │   │   └── config.py      # Settings management
│   │   ├── db/                # Database setup
│   │   │   └── session.py     # SQLAlchemy session
│   │   ├── models/            # Database models
│   │   │   └── article.py     # Article & Source models
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── article.py     # API schemas
│   │   ├── scrapers/          # Scraper implementations
│   │   │   ├── base.py        # Base scraper class
│   │   │   ├── rss.py         # RSS feed scraper
│   │   │   └── twitter.py     # Twitter scraper (placeholder)
│   │   ├── tasks/             # Background tasks
│   │   │   └── scrape.py      # Celery tasks
│   │   └── main.py            # FastAPI app entry
│   ├── Dockerfile
│   ├── pyproject.toml         # UV dependencies
│   └── README.md
├── frontend/                   # Next.js service
│   ├── app/
│   │   ├── page.tsx           # Homepage
│   │   ├── search/page.tsx    # Search page
│   │   ├── stats/page.tsx     # Statistics page
│   │   └── layout.tsx         # Root layout
│   ├── components/
│   │   ├── article-card.tsx   # Article card component
│   │   ├── news-grid.tsx      # Grid layout
│   │   └── search-bar.tsx     # Search component
│   ├── lib/
│   │   ├── api-client.ts      # Backend API client
│   │   └── types.ts           # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml          # Full stack orchestration
└── README.md                   # This file
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

**Interactive docs**: http://localhost:8000/docs

## 🐦 Twitter/X Scraping Setup

The Twitter scraper runs as a **separate service** using Playwright (headless Chromium). It's ready to use but requires configuration when you need it.

### Current Status
✅ Container built and configured  
✅ Scrapes from: @elonmusk, @OpenAI, @verge, @techcrunch, @wired  
✅ Posts tweets directly to backend API  
⏳ **Awaiting authentication setup** (Twitter login required)

### Quick Start (No Auth - Limited)
```bash
# Scraper runs automatically with docker-compose up
# Will attempt to scrape public tweets without login
# May be limited by Twitter's restrictions
```

### Full Setup (With Authentication)
Twitter requires login for full access. Add credentials to enable authenticated scraping:

1. **Edit `docker-compose.yml`** to add Twitter credentials:
   ```yaml
   twitter-scraper:
     environment:
       TWITTER_USERNAME: your_username
       TWITTER_PASSWORD: your_password
   ```

2. **Or mount a cookies file** (safer):
   ```yaml
   twitter-scraper:
     volumes:
       - ./twitter-scraper/cookies.json:/app/cookies.json
   ```

3. **Restart the scraper**:
   ```bash
   docker-compose restart twitter-scraper
   ```

### Configure Accounts
Edit `TWITTER_ACCOUNTS` in `docker-compose.yml`:
```yaml
TWITTER_ACCOUNTS: elonmusk,OpenAI,verge,techcrunch,wired,YourAccount
```

### Check Scraper Logs
```bash
docker logs -f news-twitter-scraper
```

### Alternative: Use Official Twitter API
For production, consider using the Twitter API instead:
- More reliable than web scraping
- Better rate limits
- Requires Twitter Developer account (free tier available)
- See `twitter-scraper/README.md` for details

## 📊 Data Flow

1. **Celery Beat** triggers scraping tasks every 15-30 minutes
2. **Celery Workers** execute scrapers (RSS, Twitter)
3. **Scrapers** fetch articles and normalize data
4. **Backend** stores articles in PostgreSQL (deduplicates by URL)
5. **Frontend** fetches articles via REST API
6. **Users** browse, search, and filter news

## 🚢 Deployment

### Backend Deployment Options

- **Railway**: Push backend to Railway with PostgreSQL addon
- **Render**: Deploy as Web Service + PostgreSQL instance
- **DigitalOcean**: Use App Platform or Droplet
- **Fly.io**: Deploy with Fly Postgres

### Frontend Deployment

- **Vercel** (recommended): `vercel --prod` from frontend/
- **Netlify**: Connect GitHub repo
- **Cloudflare Pages**: Static site deployment

### Environment Variables

**Backend** (Railway/Render):
```
DATABASE_URL=postgresql://...
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
# Check database connection
docker-compose logs postgres

# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Frontend can't connect to backend?

1. Check `NEXT_PUBLIC_API_URL` in `.env.local`
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check CORS settings in `backend/app/core/config.py`

### No articles showing?

```bash
# Trigger manual scrape
docker-compose exec backend python -c "from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()"

# Check celery worker logs
docker-compose logs celery-worker

# Check database
docker-compose exec postgres psql -U newsuser -d newsdb -c "SELECT COUNT(*) FROM articles;"
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
- **PostgreSQL** - Database
- **Redis** - Cache & task queue
- **Celery** - Distributed task queue
