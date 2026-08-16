"""Twitter/X profile scraper powered by Agent-Reach (Panniantong/agent-reach).

Given a list of profile URLs (e.g. https://x.com/elonmusk), fetches each
profile's most recent posts and POSTs them to the backend's /api/news/
endpoint.

Agent-Reach is installed in the image and used to provision + health-check
the Twitter backend (currently twitter-cli, per Agent-Reach's own routing -
see `agent-reach doctor`). The actual per-profile fetch shells out to
whatever CLI Agent-Reach selected, via `twitter user-posts <handle> --json`.

No browser/Chromium involved: twitter-cli talks to X's internal API directly
using cookie auth (TWITTER_AUTH_TOKEN + TWITTER_CT0).
"""
import asyncio
import json
import logging
import os
import subprocess
import sys
from urllib.parse import urlparse

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "900"))  # 15 minutes
POSTS_PER_PROFILE = int(os.getenv("POSTS_PER_PROFILE", "10"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "5"))  # seconds between profiles
CLI_TIMEOUT = int(os.getenv("CLI_TIMEOUT", "60"))  # seconds per twitter-cli call

TWITTER_AUTH_TOKEN = os.getenv("TWITTER_AUTH_TOKEN", "")
TWITTER_CT0 = os.getenv("TWITTER_CT0", "")

_PROFILE_URL_ENV_KEYS = ("TWITTER_PROFILE_URLS", "TWITTER_URLS", "TWITTER_ACCOUNTS")


def _load_profile_urls() -> list[str]:
    """Read profile URLs/handles from the first configured env var."""
    raw = ""
    for key in _PROFILE_URL_ENV_KEYS:
        raw = os.getenv(key, "")
        if raw:
            break
    return [item.strip() for item in raw.split(",") if item.strip()]


PROFILE_URLS = _load_profile_urls()


def handle_from_url(url_or_handle: str) -> str | None:
    """Extract a bare @handle from a profile URL or a raw handle string."""
    value = url_or_handle.strip().lstrip("@")
    if not value:
        return None

    if "://" not in value and "." not in value.split("/")[0]:
        # Looks like a bare handle already (no domain component).
        handle = value.split("/")[0].split("?")[0]
        return handle or None

    parsed = urlparse(value if "://" in value else f"https://{value}")
    if parsed.netloc.lower() not in ("x.com", "www.x.com", "twitter.com", "www.twitter.com"):
        logger.warning("Skipping non-Twitter/X URL: %s", url_or_handle)
        return None

    path = parsed.path.strip("/")
    if not path:
        return None
    handle = path.split("/")[0]

    reserved = {"i", "home", "explore", "notifications", "messages", "settings", "search"}
    if handle.lower() in reserved:
        logger.warning("Skipping non-profile Twitter/X URL: %s", url_or_handle)
        return None

    return handle


def log_agent_reach_status() -> None:
    """Run `agent-reach doctor --json` and log the Twitter channel status.

    Purely diagnostic: doctor only inspects installed backends and explicit
    credentials, it never triggers a live X request. This gives operators a
    quick read on whether Agent-Reach considers the Twitter backend healthy
    without duplicating its channel-selection logic here.
    """
    try:
        result = subprocess.run(
            ["agent-reach", "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("Could not run `agent-reach doctor`: %s", exc)
        return

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("agent-reach doctor produced non-JSON output")
        return

    twitter_status = report.get("twitter", {})
    logger.info(
        "Agent-Reach twitter channel: status=%s backend=%s",
        twitter_status.get("status", "unknown"),
        twitter_status.get("active_backend") or ", ".join(twitter_status.get("backends", [])),
    )
    message = twitter_status.get("message")
    if message and twitter_status.get("status") != "ok":
        logger.info("Agent-Reach says: %s", message)


def run_twitter_cli(handle: str, count: int) -> list[dict]:
    """Run `twitter user-posts <handle> --json` and return the parsed tweet list."""
    env = os.environ.copy()
    if TWITTER_AUTH_TOKEN:
        env["TWITTER_AUTH_TOKEN"] = TWITTER_AUTH_TOKEN
    if TWITTER_CT0:
        env["TWITTER_CT0"] = TWITTER_CT0

    cmd = ["twitter", "user-posts", handle, "--max", str(count), "--json"]
    logger.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        logger.error("twitter-cli timed out for @%s", handle)
        return []
    except FileNotFoundError:
        logger.error("`twitter` CLI not found on PATH. Is twitter-cli installed?")
        return []

    if result.returncode != 0:
        logger.warning(
            "twitter-cli exited %d for @%s: %s",
            result.returncode,
            handle,
            (result.stderr or result.stdout).strip()[:500],
        )
        # Fall through: twitter-cli still emits a structured JSON error to
        # stdout for --json mode, but there's nothing usable to parse.
        return []

    stdout = result.stdout.strip()
    if not stdout:
        logger.warning("Empty output from twitter-cli for @%s", handle)
        return []

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse twitter-cli JSON for @%s: %s", handle, exc)
        return []

    if isinstance(payload, dict):
        if payload.get("ok") is False:
            error = payload.get("error", {})
            logger.warning(
                "twitter-cli reported error for @%s: %s (%s)",
                handle,
                error.get("message"),
                error.get("code"),
            )
            return []
        data = payload.get("data")
        if isinstance(data, list):
            return data
        return []

    if isinstance(payload, list):
        return payload

    return []


def tweet_to_article(tweet: dict, handle: str) -> dict | None:
    """Convert a twitter-cli tweet dict into the backend's article schema."""
    tweet_id = tweet.get("id")
    text = (tweet.get("text") or "").strip()
    if not tweet_id or not text:
        return None

    author = tweet.get("author") or {}
    screen_name = author.get("screenName") or handle

    title = text if len(text) <= 100 else f"{text[:100]}..."
    title = f"@{screen_name}: {title}"

    media = tweet.get("media") or []
    image_url = None
    for item in media:
        if item.get("type") == "photo" and item.get("url"):
            image_url = item["url"]
            break

    published_at = tweet.get("createdAtISO") or tweet.get("createdAt")

    return {
        "title": title,
        "content": text,
        "url": f"https://x.com/{screen_name}/status/{tweet_id}",
        "source": "twitter",
        "author": screen_name,
        "published_at": published_at,
        "category": "twitter",
        "image_url": image_url,
    }


async def save_articles_to_backend(articles: list[dict]) -> int:
    """POST each article to the backend API. Returns count of newly saved articles."""
    if not articles:
        return 0

    saved = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for article in articles:
            try:
                response = await client.post(f"{BACKEND_URL}/api/news/", json=article)
                if response.status_code == 201:
                    saved += 1
                    logger.info("Saved: %s", article["title"][:60])
                elif response.status_code == 400:
                    logger.debug("Already exists: %s", article["url"])
                else:
                    logger.warning(
                        "Failed to save (%d): %s", response.status_code, article["url"]
                    )
            except httpx.HTTPError as exc:
                logger.error("Error posting article to backend: %s", exc)

    return saved


async def scrape_all_profiles() -> None:
    if not PROFILE_URLS:
        logger.warning("No profile URLs configured (TWITTER_PROFILE_URLS is empty). Nothing to do.")
        return

    all_articles: list[dict] = []

    for i, raw_url in enumerate(PROFILE_URLS):
        handle = handle_from_url(raw_url)
        if not handle:
            continue

        tweets = await asyncio.to_thread(run_twitter_cli, handle, POSTS_PER_PROFILE)
        logger.info("Fetched %d posts for @%s", len(tweets), handle)

        for tweet in tweets:
            article = tweet_to_article(tweet, handle)
            if article:
                all_articles.append(article)

        if i < len(PROFILE_URLS) - 1:
            await asyncio.sleep(REQUEST_DELAY)

    logger.info("Total posts scraped: %d", len(all_articles))
    saved = await save_articles_to_backend(all_articles)
    logger.info("Saved %d new posts to backend", saved)


async def main() -> None:
    logger.info("Twitter scraper (Agent-Reach) started.")
    logger.info("Profiles: %s", ", ".join(PROFILE_URLS) or "(none configured)")
    logger.info("Posts per profile: %d, interval: %ds", POSTS_PER_PROFILE, SCRAPE_INTERVAL)

    await asyncio.to_thread(log_agent_reach_status)

    if not TWITTER_AUTH_TOKEN or not TWITTER_CT0:
        logger.warning(
            "TWITTER_AUTH_TOKEN / TWITTER_CT0 not set. The Agent-Reach Twitter "
            "backend requires cookie auth and cannot fall back to a browser "
            "inside this container, so requests will fail until these are "
            "configured."
        )

    while True:
        try:
            await scrape_all_profiles()
        except Exception:
            logger.exception("Scraping run failed")

        logger.info("Waiting %ds until next scrape...", SCRAPE_INTERVAL)
        await asyncio.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        log_agent_reach_status()
        asyncio.run(scrape_all_profiles())
    else:
        asyncio.run(main())
