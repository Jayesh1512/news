// Server-only data access layer. The FastAPI service owns the shared JSON
// datastore; Server Components call it directly instead of round-tripping
// through this app's Route Handlers.
import "server-only";

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
  search_query: string | null;
  fetched_at: string;
};

export type ApiTwitterReply = {
  reply_id: string;
  root_tweet_id: string;
  account: string;
  author: string;
  author_name: string | null;
  text: string;
  url: string;
  lang: string | null;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  media_url: string | null;
  published_at: string | null;
  search_query: string | null;
  is_thread_author: boolean;
  fetched_at: string;
};

export type ApiTwitterThread = {
  post: ApiTwitterPost;
  replies: ApiTwitterReply[];
};

export type ApiTwitterProfileSource = {
  type: "post" | "reply";
  id: string;
  url: string | null;
  root_tweet_id: string | null;
};

export type ApiTwitterProfilePost = {
  tweet_id: string;
  text: string;
  url: string;
  published_at: string | null;
  lang: string | null;
  is_retweet: boolean;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  similarity: number;
  matches_topic: boolean;
  matched_context: string | null;
};

export type ApiTwitterProfileSummary = {
  overview: string;
  topic_connection: string;
  primary_topics: string[];
  key_signals: string[];
};

export type ApiTwitterProfile = {
  profile_key: string;
  topic: string;
  topic_description: string;
  context_sentences: string[];
  username: string;
  display_name: string | null;
  profile_url: string;
  discovered_from: ApiTwitterProfileSource[];
  analyzed_post_count: number;
  matching_post_count: number;
  best_similarity: number;
  similarity_threshold: number;
  embedding_model: string;
  summary: ApiTwitterProfileSummary | null;
  summary_model: string | null;
  summary_error: string | null;
  summary_generated_at: string | null;
  recent_posts: ApiTwitterProfilePost[];
  matching_posts: ApiTwitterProfilePost[];
  fetch_error: string | null;
  analysis_error: string | null;
  analyzed_at: string;
};

const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8501").replace(/\/$/, "");
const CACHE_SECONDS = 60;

export type GetArticlesParams = {
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
  hours?: number;
};

async function fetchBackend<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      next: { revalidate: CACHE_SECONDS },
    });
    if (!response.ok) {
      console.error(`Backend request failed (${response.status}): ${path}`);
      return fallback;
    }
    return (await response.json()) as T;
  } catch (error) {
    console.error(`Backend request failed: ${path}`, error);
    return fallback;
  }
}

async function fetchBackendFresh<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${BACKEND_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      console.error(`Backend request failed (${response.status}): ${path}`);
      return fallback;
    }
    return (await response.json()) as T;
  } catch (error) {
    console.error(`Backend request failed: ${path}`, error);
    return fallback;
  }
}

export async function getArticles({
  source,
  category,
  limit = 20,
  offset = 0,
  hours = 24,
}: GetArticlesParams): Promise<ApiArticle[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    hours: String(hours),
  });
  if (source) params.set("source", source);
  if (category) params.set("category", category);
  return fetchBackend<ApiArticle[]>(`/api/news/?${params}`, []);
}

export function getArticleByIdCached(id: number): Promise<ApiArticle | null> {
  return fetchBackend<ApiArticle | null>(`/api/news/${id}`, null);
}

export type GetTwitterPostsParams = {
  account?: string;
  searchQuery?: string;
  limit?: number;
  offset?: number;
};

export async function getTwitterPosts({
  account,
  searchQuery,
  limit = 20,
  offset = 0,
}: GetTwitterPostsParams): Promise<ApiTwitterPost[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (account) params.set("account", account);
  if (searchQuery) params.set("search_query", searchQuery);
  return fetchBackend<ApiTwitterPost[]>(`/api/twitter/?${params}`, []);
}

export async function getTwitterThreads({
  searchQuery,
  limit = 20,
  offset = 0,
}: Omit<GetTwitterPostsParams, "account">): Promise<ApiTwitterThread[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (searchQuery) params.set("search_query", searchQuery);
  return fetchBackend<ApiTwitterThread[]>(`/api/twitter/threads?${params}`, []);
}

export type GetTwitterProfilesParams = {
  topic?: string;
  minSimilarity?: number;
  minMatchingPosts?: number;
  limit?: number;
  offset?: number;
};

export async function getTwitterProfiles({
  topic,
  minSimilarity,
  minMatchingPosts,
  limit = 100,
  offset = 0,
}: GetTwitterProfilesParams = {}): Promise<ApiTwitterProfile[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (topic) params.set("topic", topic);
  if (minSimilarity !== undefined) params.set("min_similarity", String(minSimilarity));
  if (minMatchingPosts !== undefined) params.set("min_matching_posts", String(minMatchingPosts));
  return fetchBackendFresh<ApiTwitterProfile[]>(`/api/twitter/profiles?${params}`, []);
}
