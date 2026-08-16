"""Twitter/X scraper backed by twitter-cli (the backend Agent-Reach's Twitter
channel currently routes to - see ../../twitter-scraper/ for the standalone
container built around the same tool).

Fetches recent posts per account from app.core.constants.TWITTER_ACCOUNTS
and normalizes them for storage in Supabase (app.db.supabase_client).
"""
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Structured error codes from twitter-cli that indicate expired/invalid/
# missing cookies specifically (vs. a per-account issue like rate limiting
# or a deleted account).
AUTH_ERROR_CODES = {"not_authenticated"}


class TwitterScraper:
    """Fetches recent posts for a list of X/Twitter accounts via twitter-cli."""

    def __init__(self, source_name: str = "twitter"):
        self.source_name = source_name
        self.auth_token = settings.twitter_auth_token or os.getenv("TWITTER_AUTH_TOKEN", "")
        self.ct0 = settings.twitter_ct0 or os.getenv("TWITTER_CT0", "")

    def is_configured(self) -> bool:
        return bool(self.auth_token and self.ct0)

    def fetch_account_posts(self, handle: str, limit: int) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Run `twitter user-posts <handle> --json`.

        Returns (tweets, error_code). error_code is None on success,
        otherwise twitter-cli's structured error code (see AUTH_ERROR_CODES
        for the ones that mean expired/missing cookies).
        """
        handle = handle.lstrip("@").strip()
        if not handle:
            return [], "invalid_input"

        env = os.environ.copy()
        if self.auth_token:
            env["TWITTER_AUTH_TOKEN"] = self.auth_token
        if self.ct0:
            env["TWITTER_CT0"] = self.ct0

        cmd = ["twitter", "user-posts", handle, "--max", str(limit), "--json"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.twitter_cli_timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired:
            logger.warning("twitter-cli timed out fetching @%s", handle)
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
            return (data if isinstance(data, list) else []), None

        if isinstance(payload, list):
            return payload, None

        return [], None

    @staticmethod
    def tweet_to_record(tweet: Dict[str, Any], account: str) -> Optional[Dict[str, Any]]:
        """Normalize a twitter-cli tweet dict to a Supabase twitter_posts row."""
        tweet_id = tweet.get("id")
        text = (tweet.get("text") or "").strip()
        if not tweet_id or not text:
            return None

        author = tweet.get("author") or {}
        author_handle = author.get("screenName") or account
        metrics = tweet.get("metrics") or {}

        media_url = None
        for item in tweet.get("media") or []:
            if item.get("url"):
                media_url = item["url"]
                break

        return {
            "tweet_id": str(tweet_id),
            "account": account,
            "author": author_handle,
            "author_name": author.get("name"),
            "text": text,
            "url": f"https://x.com/{author_handle}/status/{tweet_id}",
            "is_retweet": bool(tweet.get("isRetweet", False)),
            "lang": tweet.get("lang") or None,
            "likes": int(metrics.get("likes") or 0),
            "retweets": int(metrics.get("retweets") or 0),
            "replies": int(metrics.get("replies") or 0),
            "views": int(metrics.get("views") or 0),
            "media_url": media_url,
            "published_at": tweet.get("createdAtISO") or tweet.get("createdAt") or None,
            "raw": tweet,
        }
