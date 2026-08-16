#!/bin/bash

echo "📰 News Aggregator - Quick Start"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose (v2) is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Docker Compose reads variable interpolation (${DATABASE_URL}, etc.) from
# a repo-root .env file, not backend/.env. Required: DATABASE_URL (Supabase
# Postgres connection string), SUPABASE_URL, SUPABASE_KEY - see
# backend/.env.example for the full list and where to find these values.
if [ ! -f .env ]; then
    echo "❌ No .env file at the repo root."
    echo "   This project stores everything in Supabase - there is no local"
    echo "   Postgres container. Create .env with at least:"
    echo ""
    echo "     DATABASE_URL=postgresql://postgres:[PASSWORD]@db.<project>.supabase.co:5432/postgres"
    echo "     SUPABASE_URL=https://<project>.supabase.co"
    echo "     SUPABASE_KEY=<service_role key>"
    echo ""
    echo "   See backend/.env.example for the full list and where to find"
    echo "   these values in your Supabase project (Settings > Database /"
    echo "   Settings > API)."
    exit 1
fi

if ! grep -q "^DATABASE_URL=" .env || ! grep -q "^SUPABASE_URL=" .env || ! grep -q "^SUPABASE_KEY=" .env; then
    echo "⚠️  .env exists but may be missing DATABASE_URL, SUPABASE_URL, or"
    echo "   SUPABASE_KEY. The backend will fail to start without these -"
    echo "   see backend/.env.example."
    echo ""
fi

if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend/.env.local from template..."
    cp frontend/.env.example frontend/.env.local
fi

echo ""
echo "🚀 Starting all services with Docker Compose..."
echo ""

# Each service also has its own docker-compose.<service>.yml if you only
# want to start part of the stack, e.g.:
#   docker compose -f docker-compose.backend.yml up -d --build
# See CONTAINERS.md for the exact command per container.
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Access the application:"
echo "   - Frontend: http://localhost:8502"
echo "   - Backend API: http://localhost:8501"
echo "   - API Docs: http://localhost:8501/docs"
echo ""
echo "🔍 View logs:"
echo "   docker compose logs -f"
echo ""
echo "⚙️  Trigger manual scrape:"
echo "   docker compose -f docker-compose.backend.yml exec backend python -c \"from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()\""
echo "   docker compose -f docker-compose.backend.yml exec backend python -c \"from app.tasks.scrape import scrape_twitter_accounts; print(scrape_twitter_accounts())\""
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
