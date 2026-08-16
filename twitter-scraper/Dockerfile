# Twitter Scraper - twitter-cli based (Agent-Reach's Twitter backend)
#
# No browser automation: twitter-cli talks directly to X's internal API using
# cookie auth (TWITTER_AUTH_TOKEN / TWITTER_CT0), so this is a plain Python
# image with no Chromium/Playwright dependency at all.
FROM python:3.12-slim

WORKDIR /app

# curl_cffi (a twitter-cli dependency) needs libcurl and build tooling on
# platforms without a prebuilt wheel.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY scraper.py .

ENV PYTHONUNBUFFERED=1

# Health check: the `twitter` console script must be importable/runnable.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD twitter --version || exit 1

CMD ["python", "-u", "scraper.py"]
