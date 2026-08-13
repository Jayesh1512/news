#!/bin/bash

echo "📰 News Aggregator - Quick Start"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
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

docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "⚙️  Trigger manual scrape:"
echo "   docker-compose exec backend python -c \"from app.tasks.scrape import scrape_rss_feeds; scrape_rss_feeds()\""
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
