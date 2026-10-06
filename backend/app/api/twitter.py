"""Topic-matched X posts, conversations, and discovered people."""
from functools import partial

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from typing import List, Optional

from app.core.config import settings
from app.db.json_store import get_json_store
from app.schemas.article import (
    TwitterIngestRequest,
    TwitterPostResponse,
    TwitterProfileAnalysisRequest,
    TwitterProfileResponse,
    TwitterReplyResponse,
    TwitterThreadResponse,
    TwitterTopicDiscoveryRequest,
)
from app.services.twitter_topic_context import (
    OpenAITopicContextGenerator,
    semantic_context,
)

router = APIRouter(tags=["twitter"])


@router.post("/ingest")
async def ingest_twitter_results(batch: TwitterIngestRequest):
    """Persist a topic-search batch from the internal standalone scraper."""
    if any(not item.get("tweet_id") for item in batch.posts):
        raise HTTPException(status_code=422, detail="Every X post must include tweet_id")
    if any(not item.get("reply_id") or not item.get("root_tweet_id") for item in batch.replies):
        raise HTTPException(
            status_code=422,
            detail="Every X reply must include reply_id and root_tweet_id",
        )

    store = get_json_store()
    result = {
        "posts_upserted": store.upsert_twitter_posts(batch.posts),
        "replies_upserted": store.upsert_twitter_replies(batch.replies),
    }
    should_analyze = (
        settings.twitter_profile_analysis_after_scrape
        if batch.analyze_profiles is None
        else batch.analyze_profiles
    )
    if should_analyze:
        from app.tasks.scrape import analyze_twitter_profiles

        topics = sorted(
            {
                str(item.get("search_query") or "").strip()
                for item in [*batch.posts, *batch.replies]
                if str(item.get("search_query") or "").strip()
            }
        )
        result["profile_analysis_tasks"] = [
            analyze_twitter_profiles.delay(topic=topic).id for topic in topics
        ]
    return result


@router.get("/", response_model=List[TwitterPostResponse])
async def get_twitter_posts(
    account: Optional[str] = Query(None, description="Filter by source account"),
    search_query: Optional[str] = Query(None, description="Filter by configured X query"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """Get scraped Twitter/X posts, newest first."""
    return get_json_store().list_twitter_posts(
        account=account, search_query=search_query, limit=limit, offset=offset
    )


@router.get("/replies", response_model=List[TwitterReplyResponse])
async def get_twitter_replies(
    account: Optional[str] = Query(None, description="Filter by source account"),
    root_tweet_id: Optional[str] = Query(None, description="Filter by root tweet"),
    search_query: Optional[str] = Query(None, description="Filter by configured X query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get stored conversation replies, newest first."""
    return get_json_store().list_twitter_replies(
        account=account,
        root_tweet_id=root_tweet_id,
        search_query=search_query,
        limit=limit,
        offset=offset,
    )


@router.get("/threads", response_model=List[TwitterThreadResponse])
async def get_twitter_threads(
    search_query: Optional[str] = Query(None, description="Filter by configured X query"),
    limit: int = Query(20, ge=1, le=100, description="Number of root posts"),
    offset: int = Query(0, ge=0),
    replies_limit: int = Query(100, ge=1, le=500, description="Replies per root post"),
):
    """Get topic matches grouped with the conversations fetched for them."""
    store = get_json_store()
    posts = store.list_twitter_posts(
        search_query=search_query,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "post": post,
            "replies": store.list_twitter_replies(
                root_tweet_id=post["tweet_id"],
                search_query=search_query,
                limit=replies_limit,
            ),
        }
        for post in posts
    ]


@router.get("/profiles", response_model=List[TwitterProfileResponse])
async def get_twitter_profiles(
    topic: Optional[str] = Query(None, description="Filter by analyzed topic"),
    min_similarity: Optional[float] = Query(None, ge=0, le=1),
    min_matching_posts: Optional[int] = Query(None, ge=0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List analyzed people with their recent posts and match evidence."""
    return get_json_store().list_twitter_profiles(
        topic=topic,
        min_similarity=min_similarity,
        min_matching_posts=min_matching_posts,
        limit=limit,
        offset=offset,
    )


@router.post("/profiles/analyze")
async def start_twitter_profile_analysis(request: TwitterProfileAnalysisRequest):
    """Run profile analysis inline or enqueue the independent Celery task."""
    from app.tasks.scrape import analyze_twitter_profiles

    kwargs = {
        "topic": request.topic,
        "topic_description": request.topic_description,
        "context_sentences": request.context_sentences,
        "posts_per_author": request.posts_per_author,
        "similarity_threshold": request.similarity_threshold,
    }
    if request.run_mode == "celery":
        task = analyze_twitter_profiles.delay(**kwargs)
        return {"status": "queued", "task_id": task.id}

    return await run_in_threadpool(partial(analyze_twitter_profiles.run, **kwargs))


@router.post("/topic-searches")
async def start_twitter_topic_discovery(request: TwitterTopicDiscoveryRequest):
    """Expand a topic into semantic anchors, then enqueue X discovery."""
    from app.scrapers.twitter import TwitterScraper
    from app.tasks.scrape import discover_twitter_topic

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is required to generate topic context.",
        )
    if not TwitterScraper().is_configured():
        raise HTTPException(
            status_code=503,
            detail="X credentials are not configured. Set TWITTER_AUTH_TOKEN and TWITTER_CT0.",
        )

    topic = request.topic.strip()
    generator = OpenAITopicContextGenerator(
        api_key=settings.openai_api_key,
        model=settings.twitter_profile_summary_model,
    )
    try:
        context = await run_in_threadpool(partial(generator.generate, topic))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not generate search context: {type(exc).__name__}: {exc}",
        ) from exc

    context_sentences = context["context_sentences"]
    task = discover_twitter_topic.delay(
        topic=topic,
        search_query=context["x_search_query"],
        topic_description=semantic_context(context_sentences),
        context_sentences=context_sentences,
        search_type=request.search_type,
        search_results=request.search_results,
        replies_per_post=request.replies_per_post,
        posts_per_author=request.posts_per_author,
        similarity_threshold=request.similarity_threshold,
    )
    return {
        "status": "queued",
        "task_id": task.id,
        "topic": topic,
        "x_search_query": context["x_search_query"],
        "context_sentences": context_sentences,
        "semantic_context": semantic_context(context_sentences),
        "context_model": settings.twitter_profile_summary_model,
    }


@router.get("/tasks/{task_id}")
async def get_twitter_task(task_id: str):
    """Return progress or the final result for an X discovery task."""
    from app.tasks.scrape import celery_app

    task = celery_app.AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "state": task.state,
        "ready": task.ready(),
    }
    if task.state == "PROGRESS" and isinstance(task.info, dict):
        payload["progress"] = task.info
    elif task.successful():
        payload["result"] = task.result
    elif task.failed():
        payload["error"] = f"{type(task.result).__name__}: {task.result}"
    return payload
