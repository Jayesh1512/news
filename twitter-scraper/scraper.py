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
import time
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

# Health state file consumed by the Docker HEALTHCHECK (see Dockerfile) and
# readable by operators to check auth status without grepping logs.
HEALTH_STATE_PATH = os.getenv("HEALTH_STATE_PATH", "/tmp/scraper_health.json")
# Consecutive fully-auth-failed scrape cycles before we consider the
# container unhealthy (surfaced via `docker ps` / HEALTHCHECK).
AUTH_FAILURE_CYCLES_UNHEALTHY = int(os.getenv("AUTH_FAILURE_CYCLES_UNHEALTHY", "2"))

_PROFILE_URL_ENV_KEYS = ("TWITTER_PROFILE_URLS", "TWITTER_URLS", "TWITTER_ACCOUNTS")

# Structured error codes from twitter-cli that indicate expired/invalid/
# missing cookies rather than a transient or per-profile problem.
_AUTH_ERROR_CODES = {"not_authenticated"}


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


def run_twitter_cli(handle: str, count: int) -> tuple[list[dict], str | None]:
    """Run `twitter user-posts <handle> --json`.

    Returns (tweets, error_code). error_code is None on success, otherwise
    twitter-cli's structured error code (e.g. "not_authenticated",
    "rate_limited", "not_found") - see _AUTH_ERROR_CODES for which ones
    indicate expired/missing cookies specifically.
    """
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
        return [], "timeout"
    except FileNotFoundError:
        logger.error("`twitter` CLI not found on PATH. Is twitter-cli installed?")
        return [], "cli_not_found"

    stdout = result.stdout.strip()

    if result.returncode != 0:
        error_code = None
        if stdout:
            try:
                payload = json.loads(stdout)
                if isinstance(payload, dict) and payload.get("ok") is False:
                    error_code = payload.get("error", {}).get("code")
            except json.JSONDecodeError:
                pass
        logger.warning(
            "twitter-cli exited %d for @%s: %s",
            result.returncode,
            handle,
            (result.stderr or stdout).strip()[:500],
        )
        return [], error_code or "unknown_error"

    if not stdout:
        logger.warning("Empty output from twitter-cli for @%s", handle)
        return [], "empty_output"

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse twitter-cli JSON for @%s: %s", handle, exc)
        return [], "parse_error"

    if isinstance(payload, dict):
        if payload.get("ok") is False:
            error = payload.get("error", {})
            logger.warning(
                "twitter-cli reported error for @%s: %s (%s)",
                handle,
                error.get("message"),
                error.get("code"),
            )
            return [], error.get("code") or "unknown_error"
        data = payload.get("data")
        if isinstance(data, list):
            return data, None
        return [], None

    if isinstance(payload, list):
        return payload, None

    return [], None


def _read_health_state() -> dict:
    try:
        with open(HEALTH_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_health_state(state: dict) -> None:
    state["updated_at"] = time.time()
    try:
        with open(HEALTH_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError as exc:
        logger.warning("Could not write health state to %s: %s", HEALTH_STATE_PATH, exc)


def record_cycle_result(auth_failure_count: int, total_profiles: int) -> None:
    """Track consecutive fully-auth-failed cycles and alert loudly when the
    cookies look expired/invalid (as opposed to one profile having an issue).
    """
    state = _read_health_state()
    consecutive = state.get("consecutive_auth_failure_cycles", 0)

    fully_auth_failed = total_profiles > 0 and auth_failure_count == total_profiles
    if fully_auth_failed:
        consecutive += 1
    else:
        consecutive = 0

    state["consecutive_auth_failure_cycles"] = consecutive
    state["last_cycle_auth_failures"] = auth_failure_count
    state["last_cycle_total_profiles"] = total_profiles
    state["healthy"] = consecutive < AUTH_FAILURE_CYCLES_UNHEALTHY
    _write_health_state(state)

    if fully_auth_failed:
        logger.warning(
            "AUTH CHECK: every profile failed with an auth error this cycle "
            "(%d/%d). Consecutive failed cycles: %d.",
            auth_failure_count,
            total_profiles,
            consecutive,
        )
    if consecutive >= AUTH_FAILURE_CYCLES_UNHEALTHY:
        logger.error(
            "=" * 70 + "\n"
            "TWITTER COOKIES LIKELY EXPIRED OR INVALID\n"
            "Every profile has failed with an authentication error for %d "
            "consecutive scrape cycles. TWITTER_AUTH_TOKEN / TWITTER_CT0 "
            "need to be re-exported from a logged-in x.com session "
            "(Cookie-Editor) and set in .env, then restart this container.\n"
            "See twitter-scraper/README.md > Authentication.\n" + "=" * 70,
            consecutive,
        )


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
    valid_handles: list[str] = []
    auth_failures = 0

    for raw_url in PROFILE_URLS:
        handle = handle_from_url(raw_url)
        if handle:
            valid_handles.append(handle)

    for i, handle in enumerate(valid_handles):
        tweets, error_code = await asyncio.to_thread(run_twitter_cli, handle, POSTS_PER_PROFILE)

        if error_code in _AUTH_ERROR_CODES:
            auth_failures += 1
        logger.info("Fetched %d posts for @%s", len(tweets), handle)

        for tweet in tweets:
            article = tweet_to_article(tweet, handle)
            if article:
                all_articles.append(article)

        if i < len(valid_handles) - 1:
            await asyncio.sleep(REQUEST_DELAY)

    if valid_handles:
        record_cycle_result(auth_failures, len(valid_handles))

    logger.info("Total posts scraped: %d", len(all_articles))
    saved = await save_articles_to_backend(all_articles)
    logger.info("Saved %d new posts to backend", saved)


def check_health() -> int:
    """Exit 0 if healthy, 1 if unhealthy. Used by the Docker HEALTHCHECK.

    Before the first scrape cycle completes (no state file yet), reports
    healthy - we don't want the container flagged unhealthy just because it
    hasn't scraped yet.
    """
    state = _read_health_state()
    if not state:
        print("No scrape cycles completed yet.")
        return 0
    if state.get("healthy", True):
        print(
            "OK: %d/%d profiles auth-failed last cycle, %d consecutive fully-failed cycles."
            % (
                state.get("last_cycle_auth_failures", 0),
                state.get("last_cycle_total_profiles", 0),
                state.get("consecutive_auth_failure_cycles", 0),
            )
        )
        return 0
    print(
        "UNHEALTHY: %d consecutive cycles where every profile failed auth. "
        "Twitter cookies likely expired - see logs."
        % state.get("consecutive_auth_failure_cycles", 0)
    )
    return 1


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
    if "--healthcheck" in sys.argv:
        sys.exit(check_health())
    elif "--once" in sys.argv:
        log_agent_reach_status()
        asyncio.run(scrape_all_profiles())
    else:
        asyncio.run(main())
