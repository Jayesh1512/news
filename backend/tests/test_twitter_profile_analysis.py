from types import SimpleNamespace

from app.db.json_store import JsonStore
from app.scrapers.twitter import TwitterScraper
from app.services.twitter_profile_analysis import (
    TwitterProfileAnalysisService,
    OpenAIEmbeddingClient,
    OpenAIProfileSummarizer,
    ProfileSummaryData,
    cosine_similarity,
)
from app.tasks import scrape as scrape_tasks


def _stored_post(tweet_id: str, author: str, topic: str) -> dict:
    return {
        "tweet_id": tweet_id,
        "account": author,
        "author": author,
        "author_name": author.title(),
        "text": f"Seed post from {author}",
        "url": f"https://x.com/{author}/status/{tweet_id}",
        "search_query": topic,
    }


def _stored_reply(reply_id: str, author: str, topic: str, root_id: str) -> dict:
    return {
        "reply_id": reply_id,
        "root_tweet_id": root_id,
        "account": "alice",
        "author": author,
        "author_name": author.title(),
        "text": f"Reply from {author}",
        "url": f"https://x.com/{author}/status/{reply_id}",
        "search_query": topic,
    }


def _timeline_post(tweet_id: str, author: str, text: str) -> dict:
    return {
        "id": tweet_id,
        "text": text,
        "author": {"screenName": author, "name": author.title()},
        "createdAtISO": "2026-10-07T08:00:00Z",
        "metrics": {"likes": 2, "views": 50},
    }


class KeywordEmbeddings:
    model = "test-embedding-model"

    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.casefold()
            vectors.append([1.0, 0.0] if "llm" in lowered or "inference" in lowered else [0.0, 1.0])
        return vectors


class FakeScraper:
    def __init__(self):
        self.calls = []

    def fetch_user_posts(self, username, limit):
        self.calls.append((username, limit))
        return (
            [
                _timeline_post(f"{username}-1", username, "Cheap LLM inference providers"),
                _timeline_post(f"{username}-2", username, "A completely unrelated lunch post"),
            ],
            None,
        )


class FakeSummarizer:
    model = "test-summary-model"

    def summarize(self, *, username, topic, topic_description, posts):
        return {
            "overview": f"@{username} discusses model infrastructure and pricing.",
            "topic_connection": f"One recent post directly matches {topic}.",
            "primary_topics": ["LLM inference", "provider pricing"],
            "key_signals": ["provider comparison"],
        }


def test_profile_service_analyzes_every_unique_root_and_reply_author(tmp_path):
    topic = "Cheap LLM Providers"
    store = JsonStore(tmp_path / "news.json")
    store.upsert_twitter_posts([_stored_post("100", "alice", topic)])
    store.upsert_twitter_replies(
        [
            _stored_reply("101", "alice", topic, "100"),
            _stored_reply("102", "bob", topic, "100"),
        ]
    )
    scraper = FakeScraper()
    service = TwitterProfileAnalysisService(
        store=store,
        scraper=scraper,
        embeddings=KeywordEmbeddings(),
        summarizer=FakeSummarizer(),
        sleep=lambda _: None,
    )

    result = service.analyze(
        topic=topic,
        topic_description="Affordable LLM inference",
        posts_per_author=10,
        similarity_threshold=0.70,
        request_delay_seconds=0,
    )

    assert result["candidates"] == 2
    assert result["profiles_analyzed"] == 2
    assert result["profiles_with_matches"] == 2
    assert result["summaries_generated"] == 2
    assert scraper.calls == [("alice", 10), ("bob", 10)]

    profiles = store.list_twitter_profiles(topic=topic)
    assert {profile["username"] for profile in profiles} == {"alice", "bob"}
    assert all(profile["analyzed_post_count"] == 2 for profile in profiles)
    assert all(profile["matching_post_count"] == 1 for profile in profiles)
    alice = next(profile for profile in profiles if profile["username"] == "alice")
    assert {source["type"] for source in alice["discovered_from"]} == {"post", "reply"}
    assert alice["matching_posts"][0]["text"] == "Cheap LLM inference providers"
    assert alice["summary"]["primary_topics"] == ["LLM inference", "provider pricing"]
    assert alice["summary_model"] == "test-summary-model"


def test_fetch_user_posts_builds_stable_twitter_cli_command(monkeypatch):
    scraper = TwitterScraper()
    calls = []

    def fake_run_cli(cmd, label):
        calls.append((cmd, label))
        return [], None

    monkeypatch.setattr(scraper, "_run_cli", fake_run_cli)

    posts, error = scraper.fetch_user_posts("@alice", 15)

    assert posts == []
    assert error is None
    assert calls == [
        (
            ["twitter", "user-posts", "alice", "--max", "15", "--json"],
            "recent posts for @alice",
        )
    ]


def test_cosine_similarity_handles_identical_and_orthogonal_vectors():
    assert cosine_similarity([1, 0], [1, 0]) == 1
    assert cosine_similarity([1, 0], [0, 1]) == 0


def test_openai_embedding_client_batches_inputs_with_large_model():
    calls = []

    class FakeEmbeddingsAPI:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                data=[
                    SimpleNamespace(index=1, embedding=[0.0, 1.0]),
                    SimpleNamespace(index=0, embedding=[1.0, 0.0]),
                ]
            )

    embeddings = OpenAIEmbeddingClient.__new__(OpenAIEmbeddingClient)
    embeddings.model = "text-embedding-3-large"
    embeddings.dimensions = 3072
    embeddings.client = SimpleNamespace(embeddings=FakeEmbeddingsAPI())

    result = embeddings.embed(["Topic", "Recent post"])

    assert result == [[1.0, 0.0], [0.0, 1.0]]
    assert calls == [
        {
            "model": "text-embedding-3-large",
            "input": ["Topic", "Recent post"],
            "encoding_format": "float",
            "dimensions": 3072,
        }
    ]


def test_openai_profile_summarizer_uses_structured_responses_output():
    calls = []
    parsed = ProfileSummaryData(
        overview="The author discusses inference infrastructure.",
        topic_connection="A recent post compares affordable providers.",
        primary_topics=["LLM inference"],
        key_signals=["provider comparison"],
    )

    class FakeResponsesAPI:
        def parse(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output_parsed=parsed)

    summarizer = OpenAIProfileSummarizer.__new__(OpenAIProfileSummarizer)
    summarizer.model = "gpt-6-luna"
    summarizer.client = SimpleNamespace(responses=FakeResponsesAPI())

    result = summarizer.summarize(
        username="alice",
        topic="Cheap LLM Providers",
        topic_description="Affordable LLM APIs",
        posts=[
            {
                "text": "We compared three inference providers",
                "published_at": "2026-10-07T08:00:00Z",
                "similarity": 0.82,
                "matches_topic": True,
            }
        ],
    )

    assert result == parsed.model_dump()
    assert calls[0]["model"] == "gpt-6-luna"
    assert calls[0]["reasoning"] == {"effort": "none"}
    assert calls[0]["text_format"] is ProfileSummaryData


def test_profile_analysis_is_available_as_an_independent_celery_task(monkeypatch):
    monkeypatch.setattr(scrape_tasks.settings, "openai_api_key", "test-key")
    monkeypatch.setattr(TwitterScraper, "is_configured", lambda self: True)
    monkeypatch.setattr(
        scrape_tasks,
        "run_profile_analysis",
        lambda **kwargs: {"status": "success", **kwargs},
    )

    result = scrape_tasks.analyze_twitter_profiles.run(
        topic="Cheap LLM Providers",
        topic_description="Affordable model inference",
        posts_per_author=15,
        similarity_threshold=0.6,
    )

    assert result == {
        "status": "success",
        "topic": "Cheap LLM Providers",
        "topic_description": "Affordable model inference",
        "context_sentences": None,
        "posts_per_author": 15,
        "similarity_threshold": 0.6,
    }
