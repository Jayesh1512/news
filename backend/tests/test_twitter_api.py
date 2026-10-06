from fastapi.testclient import TestClient

from app.api import twitter as twitter_api
from app.db.json_store import JsonStore
from app.main import app


def test_ingest_and_filter_topic_threads(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "news.json")
    monkeypatch.setattr(twitter_api, "get_json_store", lambda: store)
    client = TestClient(app)

    first_topic = "battery recycling"
    second_topic = "warehouse robotics"
    response = client.post(
        "/api/twitter/ingest",
        json={
            "posts": [
                {
                    "tweet_id": "1",
                    "account": "alice",
                    "author": "alice",
                    "text": "Battery recycling update",
                    "url": "https://x.com/alice/status/1",
                    "search_query": first_topic,
                },
                {
                    "tweet_id": "2",
                    "account": "carol",
                    "author": "carol",
                    "text": "Robotics update",
                    "url": "https://x.com/carol/status/2",
                    "search_query": second_topic,
                },
            ],
            "replies": [
                {
                    "reply_id": "3",
                    "root_tweet_id": "1",
                    "account": "alice",
                    "author": "bob",
                    "text": "Interesting",
                    "url": "https://x.com/bob/status/3",
                    "search_query": first_topic,
                    "is_thread_author": False,
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"posts_upserted": 2, "replies_upserted": 1}

    posts = client.get("/api/twitter/", params={"search_query": first_topic})
    replies = client.get("/api/twitter/replies", params={"search_query": first_topic})

    assert posts.status_code == 200
    assert [post["tweet_id"] for post in posts.json()] == ["1"]
    assert replies.status_code == 200
    assert [reply["reply_id"] for reply in replies.json()] == ["3"]
    assert replies.json()[0]["author"] == "bob"

    threads = client.get("/api/twitter/threads", params={"search_query": first_topic})
    assert threads.status_code == 200
    assert len(threads.json()) == 1
    assert threads.json()[0]["post"]["tweet_id"] == "1"
    assert [reply["reply_id"] for reply in threads.json()[0]["replies"]] == ["3"]


def test_ingest_rejects_reply_without_root_tweet(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "news.json")
    monkeypatch.setattr(twitter_api, "get_json_store", lambda: store)
    client = TestClient(app)

    response = client.post(
        "/api/twitter/ingest",
        json={"posts": [], "replies": [{"reply_id": "3"}]},
    )

    assert response.status_code == 422


def test_profiles_endpoint_filters_stored_analysis(tmp_path, monkeypatch):
    store = JsonStore(tmp_path / "news.json")
    monkeypatch.setattr(twitter_api, "get_json_store", lambda: store)
    client = TestClient(app)
    topic = "Cheap LLM Providers"
    store.upsert_twitter_profiles(
        [
            {
                "profile_key": f"{topic.casefold()}::alice",
                "topic": topic,
                "topic_description": "Affordable LLM inference",
                "username": "alice",
                "display_name": "Alice",
                "profile_url": "https://x.com/alice",
                "discovered_from": [],
                "analyzed_post_count": 15,
                "matching_post_count": 3,
                "best_similarity": 0.82,
                "similarity_threshold": 0.6,
                "embedding_model": "text-embedding-3-large",
                "recent_posts": [],
                "matching_posts": [],
                "fetch_error": None,
                "analysis_error": None,
                "analyzed_at": "2026-10-07T10:00:00Z",
            }
        ]
    )

    response = client.get(
        "/api/twitter/profiles",
        params={"topic": topic, "min_similarity": 0.8, "min_matching_posts": 2},
    )

    assert response.status_code == 200
    assert [profile["username"] for profile in response.json()] == ["alice"]
    assert response.json()[0]["embedding_model"] == "text-embedding-3-large"


def test_topic_search_generates_context_and_queues_discovery(monkeypatch):
    class FakeGenerator:
        def __init__(self, **kwargs):
            assert kwargs == {"api_key": "test-key", "model": "gpt-6-luna"}

        def generate(self, topic):
            assert topic == "Cheap LLM Providers"
            return {
                "x_search_query": '"cheap LLM" OR "low cost inference"',
                "context_sentences": [
                    "People compare low-cost hosted LLM APIs.",
                    "Developers discuss affordable token pricing.",
                    "Teams seek alternatives to expensive inference providers.",
                    "Posts evaluate inexpensive language model hosting.",
                    "Builders balance model quality with inference cost.",
                ],
            }

    class FakeTask:
        id = "task-123"

    captured = {}

    class FakeDiscoveryTask:
        @staticmethod
        def delay(**kwargs):
            captured.update(kwargs)
            return FakeTask()

    monkeypatch.setattr(twitter_api.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(
        twitter_api.settings, "twitter_profile_summary_model", "gpt-6-luna"
    )
    monkeypatch.setattr(twitter_api, "OpenAITopicContextGenerator", FakeGenerator)
    monkeypatch.setattr(
        "app.scrapers.twitter.TwitterScraper.is_configured", lambda self: True
    )
    monkeypatch.setattr(
        "app.tasks.scrape.discover_twitter_topic", FakeDiscoveryTask()
    )

    response = TestClient(app).post(
        "/api/twitter/topic-searches",
        json={"topic": "  Cheap LLM Providers  ", "search_results": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == "task-123"
    assert payload["x_search_query"] == '"cheap LLM" OR "low cost inference"'
    assert len(payload["context_sentences"]) == 5
    assert captured["topic"] == "Cheap LLM Providers"
    assert captured["search_results"] == 6
    assert captured["context_sentences"] == payload["context_sentences"]
