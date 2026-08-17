// Server-only data access layer: reads articles (RSS) and Twitter/X posts
// directly from Supabase (the same Postgres database + REST API the old
// FastAPI backend used - see backend/app/api/news.py and
// backend/app/api/twitter.py, which this replaces for the frontend's own
// reads). Every exported function is wrapped in `unstable_cache` so
// concurrent/rapid page loads share one Supabase round trip instead of
// hitting the database on every request ("backend level caching").
import "server-only";
import { unstable_cache } from "next/cache";
import { getSupabaseClient, isSupabaseConfigured } from "@/lib/supabase-server";

/** A backend RSS article row, as stored in the `articles` table. */
export type ApiArticle = {
  id: number;
  title: string;
  content: string | null;
  url: string;
  source: string;
  author: string | null;
  published_at: string | null;
  fetched_at: string;
  category: string | null;
  image_url: string | null;
};

/** A scraped Twitter/X post row, as stored in the `twitter_posts` table. */
export type ApiTwitterPost = {
  tweet_id: string;
  account: string;
  author: string;
  author_name: string | null;
  text: string;
  url: string;
  is_retweet: boolean;
  lang: string | null;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  media_url: string | null;
  published_at: string | null;
  fetched_at: string;
};

// How long a cached query result is served before Supabase is hit again.
// Matches the previous FastAPI setup's `next: { revalidate: 60 }` fetch
// option, so the feed still refreshes roughly once a minute without every
// request touching the database.
const CACHE_SECONDS = 60;

export type GetArticlesParams = {
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
  hours?: number;
};

/** Uncached implementation; always wrapped by `getArticles` below. */
async function fetchArticles({
  source,
  category,
  limit = 20,
  offset = 0,
  hours = 24,
}: GetArticlesParams): Promise<ApiArticle[]> {
  if (!isSupabaseConfigured()) return [];

  const cutoffIso = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
  const client = getSupabaseClient();

  let query = client
    .from("articles")
    .select("id, title, content, url, source, author, published_at, fetched_at, category, image_url")
    .gte("fetched_at", cutoffIso)
    .order("published_at", { ascending: false, nullsFirst: false })
    .order("fetched_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (source) query = query.eq("source", source);
  if (category) query = query.eq("category", category);

  const { data, error } = await query;
  if (error) {
    console.error("Supabase articles query failed:", error.message);
    return [];
  }
  return data ?? [];
}

/** Cached: articles from the last `hours`, newest first, optionally filtered. */
export const getArticles = unstable_cache(fetchArticles, ["articles"], {
  revalidate: CACHE_SECONDS,
  tags: ["articles"],
});

/** Uncached implementation; always wrapped by `getArticleByIdCached` below. */
async function fetchArticleById(id: number): Promise<ApiArticle | null> {
  if (!isSupabaseConfigured()) return null;

  const client = getSupabaseClient();
  const { data, error } = await client
    .from("articles")
    .select("id, title, content, url, source, author, published_at, fetched_at, category, image_url")
    .eq("id", id)
    .maybeSingle();

  if (error) {
    console.error("Supabase article-by-id query failed:", error.message);
    return null;
  }
  return data;
}

/** Cached: a single article by id (used by /article/[id]). */
export const getArticleByIdCached = unstable_cache(fetchArticleById, ["article-by-id"], {
  revalidate: CACHE_SECONDS,
  tags: ["articles"],
});

export type GetTwitterPostsParams = {
  account?: string;
  limit?: number;
  offset?: number;
};

/** Uncached implementation; always wrapped by `getTwitterPosts` below. */
async function fetchTwitterPosts({
  account,
  limit = 20,
  offset = 0,
}: GetTwitterPostsParams): Promise<ApiTwitterPost[]> {
  if (!isSupabaseConfigured()) return [];

  const client = getSupabaseClient();
  let query = client
    .from("twitter_posts")
    .select(
      "tweet_id, account, author, author_name, text, url, is_retweet, lang, likes, retweets, replies, views, media_url, published_at, fetched_at",
    )
    .order("published_at", { ascending: false, nullsFirst: false })
    .range(offset, offset + limit - 1);

  if (account) query = query.eq("account", account);

  const { data, error } = await query;
  if (error) {
    console.error("Supabase twitter_posts query failed:", error.message);
    return [];
  }
  return data ?? [];
}

/** Cached: Twitter/X posts, newest first, optionally filtered by account. */
export const getTwitterPosts = unstable_cache(fetchTwitterPosts, ["twitter-posts"], {
  revalidate: CACHE_SECONDS,
  tags: ["twitter-posts"],
});
