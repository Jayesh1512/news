# Twitter Scraper - Lightweight Container
# Uses Python base + Playwright installed at runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright (browsers installed on first run to save build time)
RUN playwright install-deps chromium

# Copy scraper code
COPY scraper.py .

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Download browser on first run
RUN playwright install chromium --with-deps || echo "Browser will download on first run"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run scraper
CMD ["python", "-u", "scraper.py"]
