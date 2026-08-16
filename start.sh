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

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env from template..."
    cp backend/.env.example backend/.env
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
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Access the application:"
echo "   - Frontend: http://localhost:3001"
echo "   - Backend API: http://localhost:8001"
echo "   - API Docs: http://localhost:8001/docs"
echo ""
echo "🔍 View logs:"
echo "   docker compose logs -f"
echo ""
echo "⚙️  Trigger manual scrape:"
echo "   docker compose -f docker-compose.backend.yml exec backend python -c \"from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()\""
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
