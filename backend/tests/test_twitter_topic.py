from app.db.json_store import JsonStore
from app.scrapers.twitter import TwitterScraper
from app.scrapers.twitter_cli_runner import XHomeBootstrapSession
from app.tasks import scrape as scrape_tasks


def _tweet(tweet_id: str, author: str, text: str) -> dict:
    return {
        "id": tweet_id,
        "text": text,
        "author": {"screenName": author, "name": author.title()},
        "createdAtISO": "2026-10-06T08:00:00Z",
        "metrics": {"likes": 1, "replies": 2},
    }


def test_topic_task_stores_search_result_and_full_conversation(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "news.json")
    topic = '"drone delivery" lang:en'

    monkeypatch.setattr(scrape_tasks.settings, "twitter_topic_scraper_enabled", True)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_query", topic)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_results", 2)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_type", "latest")
    monkeypatch.setattr(scrape_tasks.settings, "twitter_replies_per_post", 10)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_request_delay_seconds", 0)
    monkeypatch.setattr(scrape_tasks, "get_json_store", lambda: store)
    monkeypatch.setattr(TwitterScraper, "is_configured", lambda self: True)
    monkeypatch.setattr(
        TwitterScraper,
        "search_posts",
        lambda self, query, limit, search_type: (
            [_tweet("100", "alice", "A result about drone delivery")],
            None,
        ),
    )
    monkeypatch.setattr(
        TwitterScraper,
        "fetch_tweet_replies",
        lambda self, tweet_id, limit: (
            [
                _tweet("101", "alice", "More detail from the thread author"),
                _tweet("102", "bob", "A reply from another participant"),
            ],
            None,
        ),
    )

    result = scrape_tasks.scrape_twitter_topic.run()

    assert result == {
        "status": "success",
        "topic": topic,
        "search_query": topic,
        "search_type": "latest",
        "total_fetched": 1,
        "total_upserted": 1,
        "total_replies_fetched": 2,
        "total_replies_upserted": 2,
        "thread_errors": {},
    }
    posts = store.list_twitter_posts(search_query=topic)
    replies = store.list_twitter_replies(root_tweet_id="100", search_query=topic)
    assert [post["tweet_id"] for post in posts] == ["100"]
    assert {reply["author"] for reply in replies} == {"alice", "bob"}
    assert {reply["search_query"] for reply in replies} == {topic}
    assert {reply["author"]: reply["is_thread_author"] for reply in replies} == {
        "alice": True,
        "bob": False,
    }


def test_topic_task_skips_when_query_is_empty(monkeypatch):
    monkeypatch.setattr(scrape_tasks.settings, "twitter_topic_scraper_enabled", True)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_query", "  ")

    result = scrape_tasks.scrape_twitter_topic.run()

    assert result["status"] == "skipped"
    assert "TWITTER_SEARCH_QUERY" in result["message"]


def test_topic_task_can_run_profile_analysis_after_posts_are_stored(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "news.json")
    topic = "Cheap LLM Providers"
    monkeypatch.setattr(scrape_tasks.settings, "twitter_topic_scraper_enabled", True)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_query", topic)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_results", 1)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_search_type", "latest")
    monkeypatch.setattr(scrape_tasks.settings, "twitter_replies_per_post", 10)
    monkeypatch.setattr(scrape_tasks.settings, "twitter_request_delay_seconds", 0)
    monkeypatch.setattr(scrape_tasks, "get_json_store", lambda: store)
    monkeypatch.setattr(TwitterScraper, "is_configured", lambda self: True)
    monkeypatch.setattr(
        TwitterScraper,
        "search_posts",
        lambda self, query, limit, search_type: ([_tweet("300", "alice", topic)], None),
    )
    monkeypatch.setattr(
        TwitterScraper,
        "fetch_tweet_replies",
        lambda self, tweet_id, limit: ([_tweet("301", "bob", "A reply")], None),
    )

    def fake_profile_analysis(*, topic, **kwargs):
        assert {item["author"] for item in store.list_twitter_replies(search_query=topic)} == {"bob"}
        assert kwargs["context_sentences"] is None
        return {"status": "success", "profiles_analyzed": 2}

    monkeypatch.setattr(scrape_tasks, "run_profile_analysis", fake_profile_analysis)

    result = scrape_tasks.scrape_twitter_topic.run(analyze_profiles=True)

    assert result["profile_analysis"] == {"status": "success", "profiles_analyzed": 2}


def test_search_posts_builds_configurable_query_and_retries(monkeypatch):
    scraper = TwitterScraper()
    calls = []

    def fake_run_cli(cmd, label):
        calls.append((cmd, label))
        if len(calls) == 1:
            return [], "temporary_failure"
        return [_tweet("200", "carol", "Matched")], None

    monkeypatch.setattr(scraper, "_run_cli", fake_run_cli)

    tweets, error = scraper.search_posts("battery recycling", 7, "top")

    assert error is None
    assert tweets[0]["id"] == "200"
    assert len(calls) == 2
    assert calls[0][0] == [
        "twitter",
        "search",
        "battery recycling",
        "--type",
        "top",
        "--max",
        "7",
        "--json",
    ]


def test_twitter_cli_patch_only_redirects_x_root(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.calls = []

        def get(self, url, *args, **kwargs):
            self.calls.append((url, kwargs))
            return url

    monkeypatch.setenv("TWITTER_AUTH_TOKEN", "test-auth")
    monkeypatch.setenv("TWITTER_CT0", "test-ct0")
    session = FakeSession()
    patched = XHomeBootstrapSession(session)

    assert patched.get("https://x.com") == "https://x.com/home"
    assert patched.get("https://x.com/") == "https://x.com/home"
    assert patched.get("https://x.com/i/api/graphql/example") == (
        "https://x.com/i/api/graphql/example"
    )
    assert session.calls == [
        ("https://x.com/home", {"headers": {"Cookie": "auth_token=test-auth; ct0=test-ct0"}}),
        ("https://x.com/home", {"headers": {"Cookie": "auth_token=test-auth; ct0=test-ct0"}}),
        ("https://x.com/i/api/graphql/example", {}),
    ]
