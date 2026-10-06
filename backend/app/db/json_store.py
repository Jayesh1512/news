"""Atomic JSON-file persistence for articles, sources, and Twitter data."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from app.core.config import settings


T = TypeVar("T")


class DuplicateRecordError(ValueError):
    """Raised when a unique record already exists in the JSON store."""


def _empty_store() -> dict[str, Any]:
    return {
        "articles": [],
        "sources": [],
        "twitter_posts": [],
        "twitter_replies": [],
        "twitter_profiles": [],
        "updated_at": None,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class JsonStore:
    """A small process-safe datastore backed by one JSON file.

    Writers hold an advisory lock and replace the file atomically, so the API,
    Celery worker, and standalone scraper cannot leave a partially written
    document when they update it at the same time.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")

    @contextmanager
    def _lock(self, *, exclusive: bool) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock_file:
            mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(lock_file.fileno(), mode)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.exists():
            return _empty_store()
        with self.path.open(encoding="utf-8") as data_file:
            data = json.load(data_file)
        if not isinstance(data, dict):
            raise ValueError(f"JSON datastore must contain an object: {self.path}")
        empty = _empty_store()
        for key, default in empty.items():
            data.setdefault(key, default)
        return data

    def _write_unlocked(self, data: dict[str, Any]) -> None:
        data["updated_at"] = _utc_now()
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                json.dump(_json_safe(data), temp_file, ensure_ascii=False, indent=2)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_path = Path(temp_file.name)
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()

    def ensure_exists(self) -> None:
        with self._lock(exclusive=True):
            if not self.path.exists():
                self._write_unlocked(_empty_store())

    def read(self) -> dict[str, Any]:
        with self._lock(exclusive=False):
            return self._read_unlocked()

    def _mutate(self, callback: Callable[[dict[str, Any]], T]) -> T:
        with self._lock(exclusive=True):
            data = self._read_unlocked()
            result = callback(data)
            self._write_unlocked(data)
            return result

    def list_articles(
        self,
        *,
        source: str | None = None,
        category: str | None = None,
        hours: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        articles = list(self.read()["articles"])
        if hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            articles = [
                item
                for item in articles
                if (fetched := _parse_datetime(item.get("fetched_at"))) is not None
                and fetched >= cutoff
            ]
        if source:
            articles = [item for item in articles if item.get("source") == source]
        if category:
            articles = [item for item in articles if item.get("category") == category]
        articles.sort(
            key=lambda item: _parse_datetime(item.get("published_at"))
            or _parse_datetime(item.get("fetched_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return articles[offset : offset + limit]

    def get_article(self, article_id: int) -> dict[str, Any] | None:
        return next(
            (item for item in self.read()["articles"] if item.get("id") == article_id),
            None,
        )

    def search_articles(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        needle = query.casefold()
        matches = [
            item
            for item in self.read()["articles"]
            if needle in str(item.get("title") or "").casefold()
            or needle in str(item.get("content") or "").casefold()
        ]
        matches.sort(
            key=lambda item: _parse_datetime(item.get("fetched_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return matches[:limit]

    def add_article(self, article: dict[str, Any]) -> dict[str, Any]:
        def add(data: dict[str, Any]) -> dict[str, Any]:
            if any(item.get("url") == article.get("url") for item in data["articles"]):
                raise DuplicateRecordError("Article with this URL already exists")
            next_id = max((int(item.get("id", 0)) for item in data["articles"]), default=0) + 1
            record = _json_safe(article)
            record.update({"id": next_id, "fetched_at": _utc_now()})
            data["articles"].append(record)
            return record

        return self._mutate(add)

    def add_articles(self, articles: list[dict[str, Any]]) -> int:
        def add(data: dict[str, Any]) -> int:
            known_urls = {item.get("url") for item in data["articles"]}
            next_id = max((int(item.get("id", 0)) for item in data["articles"]), default=0) + 1
            saved = 0
            for article in articles:
                if not article.get("url") or article.get("url") in known_urls:
                    continue
                record = _json_safe(article)
                record.update({"id": next_id, "fetched_at": _utc_now()})
                data["articles"].append(record)
                known_urls.add(record["url"])
                next_id += 1
                saved += 1
            return saved

        return self._mutate(add)

    def list_sources(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        sources = list(self.read()["sources"])
        if active_only:
            sources = [item for item in sources if item.get("is_active", True)]
        return sources

    def record_source(self, name: str, platform: str, url: str | None = None) -> None:
        def upsert(data: dict[str, Any]) -> None:
            now = _utc_now()
            existing = next((item for item in data["sources"] if item.get("name") == name), None)
            if existing:
                existing.update({"platform": platform, "url": url, "last_scraped_at": now})
                return
            next_id = max((int(item.get("id", 0)) for item in data["sources"]), default=0) + 1
            data["sources"].append(
                {
                    "id": next_id,
                    "name": name,
                    "platform": platform,
                    "url": url,
                    "is_active": True,
                    "last_scraped_at": now,
                    "created_at": now,
                }
            )

        self._mutate(upsert)

    def _upsert_records(self, collection: str, key: str, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0

        def upsert(data: dict[str, Any]) -> int:
            existing = {str(item[key]): item for item in data[collection] if item.get(key) is not None}
            for incoming in records:
                record = _json_safe(incoming)
                record_key = str(record[key])
                current = existing.get(record_key)
                if current:
                    fetched_at = current.get("fetched_at") or _utc_now()
                    current.update(record)
                    current["fetched_at"] = fetched_at
                else:
                    record.setdefault("fetched_at", _utc_now())
                    data[collection].append(record)
                    existing[record_key] = record
            return len(records)

        return self._mutate(upsert)

    def upsert_twitter_posts(self, records: list[dict[str, Any]]) -> int:
        return self._upsert_records("twitter_posts", "tweet_id", records)

    def upsert_twitter_replies(self, records: list[dict[str, Any]]) -> int:
        return self._upsert_records("twitter_replies", "reply_id", records)

    def upsert_twitter_profiles(self, records: list[dict[str, Any]]) -> int:
        return self._upsert_records("twitter_profiles", "profile_key", records)

    def list_twitter_posts(
        self,
        *,
        account: str | None = None,
        search_query: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        posts = list(self.read()["twitter_posts"])
        if account:
            posts = [item for item in posts if item.get("account") == account]
        if search_query:
            posts = [item for item in posts if item.get("search_query") == search_query]
        posts.sort(
            key=lambda item: _parse_datetime(item.get("published_at"))
            or _parse_datetime(item.get("fetched_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return posts[offset : offset + limit]

    def list_twitter_replies(
        self,
        *,
        account: str | None = None,
        root_tweet_id: str | None = None,
        search_query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        replies = list(self.read()["twitter_replies"])
        if account:
            replies = [item for item in replies if item.get("account") == account]
        if root_tweet_id:
            replies = [item for item in replies if item.get("root_tweet_id") == root_tweet_id]
        if search_query:
            replies = [item for item in replies if item.get("search_query") == search_query]
        replies.sort(
            key=lambda item: _parse_datetime(item.get("published_at"))
            or _parse_datetime(item.get("fetched_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return replies[offset : offset + limit]

    def list_twitter_profile_candidates(
        self, *, search_query: str
    ) -> list[dict[str, Any]]:
        """Return every unique author discovered in matching roots and replies.

        The source records are retained so profile results can explain exactly
        which topic posts or replies led to each person.
        """
        data = self.read()
        candidates: dict[str, dict[str, Any]] = {}

        def collect(item: dict[str, Any], *, source_type: str, source_id: str) -> None:
            if item.get("search_query") != search_query:
                return
            username = str(item.get("author") or "").lstrip("@").strip()
            if not username:
                return
            key = username.casefold()
            candidate = candidates.setdefault(
                key,
                {
                    "username": username,
                    "display_name": item.get("author_name"),
                    "discovered_from": [],
                },
            )
            if not candidate.get("display_name") and item.get("author_name"):
                candidate["display_name"] = item["author_name"]
            candidate["discovered_from"].append(
                {
                    "type": source_type,
                    "id": str(source_id),
                    "url": item.get("url"),
                    "root_tweet_id": item.get("root_tweet_id"),
                }
            )

        for post in data["twitter_posts"]:
            collect(post, source_type="post", source_id=str(post.get("tweet_id") or ""))
        for reply in data["twitter_replies"]:
            collect(reply, source_type="reply", source_id=str(reply.get("reply_id") or ""))

        return sorted(candidates.values(), key=lambda item: item["username"].casefold())

    def list_twitter_profiles(
        self,
        *,
        topic: str | None = None,
        min_similarity: float | None = None,
        min_matching_posts: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        profiles = list(self.read()["twitter_profiles"])
        if topic:
            profiles = [item for item in profiles if item.get("topic") == topic]
        if min_similarity is not None:
            profiles = [
                item
                for item in profiles
                if float(item.get("best_similarity") or 0) >= min_similarity
            ]
        if min_matching_posts is not None:
            profiles = [
                item
                for item in profiles
                if int(item.get("matching_post_count") or 0) >= min_matching_posts
            ]
        profiles.sort(
            key=lambda item: (
                float(item.get("best_similarity") or 0),
                int(item.get("matching_post_count") or 0),
            ),
            reverse=True,
        )
        return profiles[offset : offset + limit]


@lru_cache(maxsize=1)
def get_json_store() -> JsonStore:
    return JsonStore(settings.json_data_path)
