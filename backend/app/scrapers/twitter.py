"""Twitter/X scraper backed by twitter-cli (the backend Agent-Reach's Twitter
channel currently routes to - see ../../twitter-scraper/ for the standalone
container built around the same tool).

Searches X for a configurable topic and normalizes matching posts for the
shared JSON datastore. It also opens each result via `twitter tweet <id>`
and stores the associated conversation replies from every participant.
"""
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dateutil import parser as date_parser

from app.core.config import settings

logger = logging.getLogger(__name__)

# Structured error codes from twitter-cli that indicate expired/invalid/
# missing cookies specifically (vs. a per-account issue like rate limiting
# or a deleted account).
AUTH_ERROR_CODES = {"not_authenticated"}


class TwitterScraper:
    """Searches X and fetches result threads via twitter-cli."""

    def __init__(self, source_name: str = "twitter"):
        self.source_name = source_name
        self.auth_token = settings.twitter_auth_token or os.getenv("TWITTER_AUTH_TOKEN", "")
        self.ct0 = settings.twitter_ct0 or os.getenv("TWITTER_CT0", "")

    def is_configured(self) -> bool:
        return bool(self.auth_token and self.ct0)

    def _run_cli(self, cmd: List[str], label: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Run a `twitter ... --json` command and parse its structured output.

        Shared by search_posts (`search`) and fetch_tweet_replies (`tweet`) -
        both return a list under `data` in the same envelope
        (see twitter-cli's SCHEMA.md). `label` is only used for log messages.

        Returns (items, error_code). error_code is None on success, otherwise
        twitter-cli's structured error code (see AUTH_ERROR_CODES for the
        ones that mean expired/missing cookies).
        """
        env = os.environ.copy()
        if self.auth_token:
            env["TWITTER_AUTH_TOKEN"] = self.auth_token
        if self.ct0:
            env["TWITTER_CT0"] = self.ct0

        # Run through our local wrapper so ClientTransaction bootstraps from
        # x.com/home (the root page no longer exposes the required bundle).
        if cmd and cmd[0] == "twitter":
            cmd = [
                sys.executable,
                "-m",
                "app.scrapers.twitter_cli_runner",
                *cmd[1:],
            ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.twitter_cli_timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired:
            logger.warning("twitter-cli timed out fetching %s", label)
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
            logger.error("Failed to parse twitter-cli JSON for %s: %s", label, exc)
            return [], "parse_error"

        if isinstance(payload, dict):
            if payload.get("ok") is False:
                error = payload.get("error", {})
                logger.warning(
                    "twitter-cli reported error for %s: %s (%s)",
                    label,
                    error.get("message"),
                    error.get("code"),
                )
                return [], error.get("code") or "unknown_error"
            data = payload.get("data")
            return (data if isinstance(data, list) else []), None

        if isinstance(payload, list):
            return payload, None

        return [], None

    def search_posts(
        self,
        query: str,
        limit: int,
        search_type: str = "latest",
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Run `twitter search <query> --type <type> --json`.

        Search is retried once because X's search GraphQL operation is less
        stable than timeline/thread reads. Returns (tweets, error_code).
        """
        query = query.strip()
        if not query:
            return [], "invalid_input"

        allowed_types = {"top", "latest", "photos", "videos"}
        if search_type not in allowed_types:
            return [], "invalid_search_type"

        cmd = [
            "twitter",
            "search",
            query,
            "--type",
            search_type,
            "--max",
            str(limit),
            "--json",
        ]
        result: tuple[List[Dict[str, Any]], Optional[str]] = ([], "unknown_error")
        for attempt in range(2):
            result = self._run_cli(cmd, f'search query "{query}"')
            if result[1] is None:
                return result
            if attempt == 0:
                logger.warning("X search failed; retrying once (error=%s)", result[1])
        return result

    def fetch_tweet_replies(self, tweet_id: str, limit: int) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Run `twitter tweet <tweet_id> --json` and return just the replies.

        `twitter tweet` returns the focal tweet itself plus its conversation
        thread under `data` (a flat list: [focal_tweet, *replies]) - see
        twitter-cli's `tweet` command / SCHEMA.md. We drop the first item
        (the matched tweet, already stored via search_posts) and hand
        back only the replies.

        Returns (replies, error_code) - see _run_cli.
        """
        tweet_id = str(tweet_id).strip()
        if not tweet_id:
            return [], "invalid_input"

        cmd = ["twitter", "tweet", tweet_id, "--max", str(limit), "--json"]
        items, error_code = self._run_cli(cmd, f"tweet {tweet_id}")
        if error_code:
            return [], error_code

        # First item is the focal tweet itself, not a reply.
        replies = [item for item in items if str(item.get("id")) != tweet_id]
        return replies, None

    def fetch_user_posts(
        self, username: str, limit: int
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch a candidate author's recent timeline via ``twitter user-posts``.

        The command is one of twitter-cli's stable read paths. Credentials are
        passed by :meth:`_run_cli` in the child-process environment and never
        interpolated into command arguments or logs.
        """
        username = username.lstrip("@").strip()
        if not username:
            return [], "invalid_input"
        if limit < 1:
            return [], "invalid_limit"

        return self._run_cli(
            ["twitter", "user-posts", username, "--max", str(limit), "--json"],
            f"recent posts for @{username}",
        )

    @staticmethod
    def tweet_to_record(
        tweet: Dict[str, Any],
        account: str | None = None,
        max_age_hours: Optional[float] = None,
        search_query: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Normalize a twitter-cli tweet dict to a JSON twitter_posts record.

        Returns None (dropped) if the tweet is missing required fields, or
        if `max_age_hours` is set and the tweet's published_at is older than
        that many hours - stale posts never reach the database.
        """
        tweet_id = tweet.get("id")
        text = (tweet.get("text") or "").strip()
        if not tweet_id or not text:
            return None

        published_raw = tweet.get("createdAtISO") or tweet.get("createdAt") or None

        if max_age_hours is not None:
            if not published_raw:
                # No timestamp to judge freshness by - safer to drop than
                # to silently let an unknown-age post through the filter.
                logger.debug("Dropping tweet %s: no published_at to check age", tweet_id)
                return None
            try:
                published_dt = date_parser.parse(published_raw)
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError) as exc:
                logger.debug("Dropping tweet %s: unparseable published_at %r (%s)", tweet_id, published_raw, exc)
                return None

            age = datetime.now(timezone.utc) - published_dt
            if age > timedelta(hours=max_age_hours):
                logger.debug(
                    "Dropping tweet %s (@%s): published %.1fh ago, older than max_age_hours=%s",
                    tweet_id, account or "unknown", age.total_seconds() / 3600, max_age_hours,
                )
                return None

        author = tweet.get("author") or {}
        author_handle = (author.get("screenName") or account or "unknown").lstrip("@")
        source_account = (account or author_handle).lstrip("@")
        metrics = tweet.get("metrics") or {}

        media_url = None
        for item in tweet.get("media") or []:
            if item.get("url"):
                media_url = item["url"]
                break

        return {
            "tweet_id": str(tweet_id),
            "account": source_account,
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
            "published_at": published_raw,
            "search_query": search_query,
            "raw": tweet,
        }

    @staticmethod
    def reply_to_record(
        reply: Dict[str, Any],
        root_author: str,
        root_tweet_id: str,
        search_query: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """Normalize a twitter-cli reply dict to a JSON twitter_replies record.

        Keeps replies from every participant so callers receive the complete
        conversation associated with a search result. `account` remains the
        root author's handle, while `author` identifies each reply author.
        """
        reply_id = reply.get("id")
        text = (reply.get("text") or "").strip()
        if not reply_id or not text:
            return None

        author = reply.get("author") or {}
        author_handle = (author.get("screenName") or "").lstrip("@").strip()
        if not author_handle:
            return None

        published_raw = reply.get("createdAtISO") or reply.get("createdAt") or None
        metrics = reply.get("metrics") or {}

        media_url = None
        for item in reply.get("media") or []:
            if item.get("url"):
                media_url = item["url"]
                break

        return {
            "reply_id": str(reply_id),
            "root_tweet_id": str(root_tweet_id),
            "account": root_author.lstrip("@").strip(),
            "author": author_handle,
            "author_name": author.get("name"),
            "text": text,
            "url": f"https://x.com/{author_handle}/status/{reply_id}",
            "lang": reply.get("lang") or None,
            "likes": int(metrics.get("likes") or 0),
            "retweets": int(metrics.get("retweets") or 0),
            "replies": int(metrics.get("replies") or 0),
            "views": int(metrics.get("views") or 0),
            "media_url": media_url,
            "published_at": published_raw,
            "search_query": search_query,
            "is_thread_author": author_handle.casefold() == root_author.lstrip("@").strip().casefold(),
            "raw": reply,
        }
