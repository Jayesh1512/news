"""Configurable X topic search and conversation scraper.

Agent-Reach diagnoses the active Twitter backend (currently twitter-cli).
Each cycle searches for TWITTER_SEARCH_QUERY, opens every matching post's
conversation, and sends the normalized batch to FastAPI's JSON datastore.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any

import httpx


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
SEARCH_QUERY = os.getenv("TWITTER_SEARCH_QUERY", "").strip()
SEARCH_RESULTS = int(os.getenv("TWITTER_SEARCH_RESULTS", "10"))
SEARCH_TYPE = os.getenv("TWITTER_SEARCH_TYPE", "latest").strip().lower()
THREAD_REPLIES = int(os.getenv("TWITTER_REPLIES_PER_POST", "20"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "900"))
REQUEST_DELAY = float(os.getenv("TWITTER_REQUEST_DELAY_SECONDS", "2"))
CLI_TIMEOUT = int(os.getenv("CLI_TIMEOUT", "60"))

TWITTER_AUTH_TOKEN = os.getenv("TWITTER_AUTH_TOKEN", "")
TWITTER_CT0 = os.getenv("TWITTER_CT0", "")

HEALTH_STATE_PATH = os.getenv("HEALTH_STATE_PATH", "/tmp/scraper_health.json")
AUTH_FAILURE_CYCLES_UNHEALTHY = int(os.getenv("AUTH_FAILURE_CYCLES_UNHEALTHY", "2"))
AUTH_ERROR_CODES = {"not_authenticated"}
SEARCH_TYPES = {"top", "latest", "photos", "videos"}


def log_agent_reach_status() -> None:
    """Log Agent-Reach's diagnostic view without exposing credentials."""
    try:
        result = subprocess.run(
            ["agent-reach", "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        report = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Could not read Agent-Reach status: %s", exc)
        return

    twitter_status = report.get("twitter", {})
    logger.info(
        "Agent-Reach Twitter channel: status=%s backend=%s",
        twitter_status.get("status", "unknown"),
        twitter_status.get("active_backend")
        or ", ".join(twitter_status.get("backends", [])),
    )


def run_cli(cmd: list[str], label: str) -> tuple[list[dict[str, Any]], str | None]:
    """Run a structured twitter-cli command and return (items, error_code)."""
    env = os.environ.copy()
    if TWITTER_AUTH_TOKEN:
        env["TWITTER_AUTH_TOKEN"] = TWITTER_AUTH_TOKEN
    if TWITTER_CT0:
        env["TWITTER_CT0"] = TWITTER_CT0

    if cmd and cmd[0] == "twitter":
        cmd = [sys.executable, "-m", "twitter_cli_runner", *cmd[1:]]

    logger.info("Running X request: %s", label)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        logger.error("twitter-cli timed out for %s", label)
        return [], "timeout"
    except FileNotFoundError:
        logger.error("`twitter` CLI not found on PATH")
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
            "twitter-cli exited %d for %s: %s",
            result.returncode,
            label,
            (result.stderr or stdout).strip()[:500],
        )
        return [], error_code or "unknown_error"

    if not stdout:
        return [], "empty_output"
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("Invalid twitter-cli JSON for %s: %s", label, exc)
        return [], "parse_error"

    if isinstance(payload, dict):
        if payload.get("ok") is False:
            return [], payload.get("error", {}).get("code") or "unknown_error"
        data = payload.get("data")
        return (data if isinstance(data, list) else []), None
    if isinstance(payload, list):
        return payload, None
    return [], None


def search_posts() -> tuple[list[dict[str, Any]], str | None]:
    if not SEARCH_QUERY:
        return [], "missing_search_query"
    if SEARCH_TYPE not in SEARCH_TYPES:
        return [], "invalid_search_type"
    cmd = [
        "twitter",
        "search",
        SEARCH_QUERY,
        "--type",
        SEARCH_TYPE,
        "--max",
        str(SEARCH_RESULTS),
        "--json",
    ]
    result: tuple[list[dict[str, Any]], str | None] = ([], "unknown_error")
    for attempt in range(2):
        result = run_cli(cmd, f'search query "{SEARCH_QUERY}"')
        if result[1] is None:
            return result
        if attempt == 0:
            logger.warning("X search failed; retrying once (error=%s)", result[1])
    return result


def fetch_thread(tweet_id: str) -> tuple[list[dict[str, Any]], str | None]:
    items, error_code = run_cli(
        ["twitter", "tweet", str(tweet_id), "--max", str(THREAD_REPLIES), "--json"],
        f"thread {tweet_id}",
    )
    if error_code:
        return [], error_code
    return [item for item in items if str(item.get("id")) != str(tweet_id)], None


def _metrics(item: dict[str, Any]) -> dict[str, int]:
    metrics = item.get("metrics") or {}
    return {
        "likes": int(metrics.get("likes") or 0),
        "retweets": int(metrics.get("retweets") or 0),
        "replies": int(metrics.get("replies") or 0),
        "views": int(metrics.get("views") or 0),
    }


def _media_url(item: dict[str, Any]) -> str | None:
    for media in item.get("media") or []:
        if media.get("url"):
            return media["url"]
    return None


def post_to_record(tweet: dict[str, Any]) -> dict[str, Any] | None:
    tweet_id = tweet.get("id")
    text = (tweet.get("text") or "").strip()
    author = tweet.get("author") or {}
    author_handle = (author.get("screenName") or "").lstrip("@").strip()
    if not tweet_id or not text or not author_handle:
        return None
    return {
        "tweet_id": str(tweet_id),
        "account": author_handle,
        "author": author_handle,
        "author_name": author.get("name"),
        "text": text,
        "url": f"https://x.com/{author_handle}/status/{tweet_id}",
        "is_retweet": bool(tweet.get("isRetweet", False)),
        "lang": tweet.get("lang") or None,
        **_metrics(tweet),
        "media_url": _media_url(tweet),
        "published_at": tweet.get("createdAtISO") or tweet.get("createdAt"),
        "search_query": SEARCH_QUERY,
        "raw": tweet,
    }


def reply_to_record(
    reply: dict[str, Any], root_tweet_id: str, root_author: str
) -> dict[str, Any] | None:
    reply_id = reply.get("id")
    text = (reply.get("text") or "").strip()
    author = reply.get("author") or {}
    author_handle = (author.get("screenName") or "").lstrip("@").strip()
    if not reply_id or not text or not author_handle:
        return None
    return {
        "reply_id": str(reply_id),
        "root_tweet_id": str(root_tweet_id),
        "account": root_author,
        "author": author_handle,
        "author_name": author.get("name"),
        "text": text,
        "url": f"https://x.com/{author_handle}/status/{reply_id}",
        "lang": reply.get("lang") or None,
        **_metrics(reply),
        "media_url": _media_url(reply),
        "published_at": reply.get("createdAtISO") or reply.get("createdAt"),
        "search_query": SEARCH_QUERY,
        "is_thread_author": author_handle.casefold() == root_author.casefold(),
        "raw": reply,
    }


async def ingest_batch(posts: list[dict[str, Any]], replies: list[dict[str, Any]]) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/twitter/ingest",
            json={"posts": posts, "replies": replies},
        )
        response.raise_for_status()
        return response.json()


def _read_health_state() -> dict:
    try:
        with open(HEALTH_STATE_PATH, encoding="utf-8") as state_file:
            return json.load(state_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_health_state(error_code: str | None) -> None:
    state = _read_health_state()
    consecutive = int(state.get("consecutive_auth_failure_cycles", 0))
    consecutive = consecutive + 1 if error_code in AUTH_ERROR_CODES else 0
    state.update(
        {
            "consecutive_auth_failure_cycles": consecutive,
            "last_error_code": error_code,
            "healthy": consecutive < AUTH_FAILURE_CYCLES_UNHEALTHY,
            "updated_at": time.time(),
        }
    )
    try:
        with open(HEALTH_STATE_PATH, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file)
    except OSError as exc:
        logger.warning("Could not write health state: %s", exc)


async def scrape_topic() -> dict[str, Any]:
    if not SEARCH_QUERY:
        logger.warning("TWITTER_SEARCH_QUERY is empty; nothing to search")
        return {"status": "skipped", "error_code": "missing_search_query"}

    tweets, error_code = await asyncio.to_thread(search_posts)
    _write_health_state(error_code)
    if error_code:
        return {"status": "search_failed", "error_code": error_code}

    posts = [record for tweet in tweets if (record := post_to_record(tweet))]
    replies: list[dict[str, Any]] = []
    thread_errors: dict[str, str] = {}
    for index, post in enumerate(posts):
        thread, thread_error = await asyncio.to_thread(fetch_thread, post["tweet_id"])
        if thread_error:
            thread_errors[post["tweet_id"]] = thread_error
        else:
            replies.extend(
                record
                for item in thread
                if (record := reply_to_record(item, post["tweet_id"], post["author"]))
            )
        if index < len(posts) - 1:
            await asyncio.sleep(REQUEST_DELAY)

    ingested = await ingest_batch(posts, replies)
    result = {
        "status": "success",
        "search_query": SEARCH_QUERY,
        "matches": len(posts),
        "conversation_replies": len(replies),
        "thread_errors": thread_errors,
        **ingested,
    }
    logger.info("X topic scrape complete: %s", result)
    return result


def check_health() -> int:
    state = _read_health_state()
    if not state or state.get("healthy", True):
        print("OK: X topic scraper is healthy")
        return 0
    print("UNHEALTHY: X cookies failed authentication repeatedly")
    return 1


async def main() -> None:
    logger.info("X topic scraper started: query=%r type=%s", SEARCH_QUERY, SEARCH_TYPE)
    await asyncio.to_thread(log_agent_reach_status)
    if not TWITTER_AUTH_TOKEN or not TWITTER_CT0:
        logger.warning("TWITTER_AUTH_TOKEN / TWITTER_CT0 are not set")

    while True:
        try:
            await scrape_topic()
        except Exception:
            logger.exception("X topic scrape failed")
        logger.info("Waiting %ds until next search", SCRAPE_INTERVAL)
        await asyncio.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    if "--healthcheck" in sys.argv:
        sys.exit(check_health())
    if "--once" in sys.argv:
        log_agent_reach_status()
        print(json.dumps(asyncio.run(scrape_topic()), indent=2))
    else:
        asyncio.run(main())
