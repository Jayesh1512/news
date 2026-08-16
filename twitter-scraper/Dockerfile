# Twitter Scraper - Playwright + Chromium
#
# Uses Microsoft's official Playwright image, which already ships Chromium
# and all of its OS-level dependencies pre-installed and version-matched.
# This avoids the apt package-name churn (e.g. ttf-unifont vs fonts-unifont)
# that breaks `playwright install-deps` on plain Debian/Ubuntu base images.
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages (Chromium + deps already present in the base image)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy scraper code
COPY scraper.py .

# Environment defaults
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run scraper
CMD ["python", "-u", "scraper.py"]
