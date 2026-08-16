// Real news data: fetches RSS articles and Twitter posts from the backend
// API and normalizes them into a single feed. No more mock data - see
// git history for the old hardcoded `articles` array this replaced.

const API_URL_SERVER = process.env.API_URL_SERVER ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8501";

export const categories = [
  "Home",
  "World",
  "Business",
  "Technology",
  "Sports",
  "Science",
  "Culture",
  "Twitter/X",
] as const;

/** A backend RSS article, as returned by GET /api/news. */
type ApiArticle = {
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

/** A backend Twitter/X post, as returned by GET /api/twitter. */
type ApiTwitterPost = {
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

/**
 * Unified feed item shown in the UI. RSS articles render with an internal
 * `/article/[id]` link; Twitter posts render with an external link to X
 * (there's no local detail page for a tweet).
 */
export type FeedItem = {
  id: string;
  kind: "article" | "tweet";
  title: string;
  excerpt: string;
  category: string;
  author: string;
  publishedAt: string;
  /** ISO timestamp used for sorting; publishedAt above is the display string. */
  sortTime: number;
  href: string;
  external: boolean;
};

function articleHref(id: number) {
  return `/article/${id}`;
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diffMs = Date.now() - then;
  const diffMin = Math.round(diffMs / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

function articleToFeedItem(article: ApiArticle): FeedItem {
  const timeSource = article.published_at ?? article.fetched_at;
  const plainContent = (article.content ?? "").replace(/<[^>]*>/g, "").trim();
  return {
    id: String(article.id),
    kind: "article",
    title: article.title,
    excerpt: plainContent.slice(0, 220) || article.title,
    category: article.category ?? article.source,
    author: article.author ?? article.source,
    publishedAt: formatRelativeTime(timeSource),
    sortTime: new Date(timeSource).getTime() || 0,
    href: articleHref(article.id),
    external: false,
  };
}

function tweetToFeedItem(tweet: ApiTwitterPost): FeedItem {
  const timeSource = tweet.published_at ?? tweet.fetched_at;
  return {
    id: `tweet-${tweet.tweet_id}`,
    kind: "tweet",
    title: tweet.text.length > 140 ? `${tweet.text.slice(0, 137)}...` : tweet.text,
    excerpt: tweet.text,
    category: "Twitter/X",
    author: tweet.author_name ? `${tweet.author_name} (@${tweet.author})` : `@${tweet.author}`,
    publishedAt: formatRelativeTime(timeSource),
    sortTime: new Date(timeSource).getTime() || 0,
    href: tweet.url,
    external: true,
  };
}

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL_SERVER}${path}`, {
      // Revalidate frequently so newly-scraped RSS/Twitter data shows up
      // without a full rebuild - see Next.js 16 fetching-data guide.
      next: { revalidate: 60 },
    });
    if (!res.ok) {
      console.error(`API request failed: ${path} -> ${res.status}`);
      return null;
    }
    return (await res.json()) as T;
  } catch (err) {
    console.error(`API request errored: ${path}`, err);
    return null;
  }
}

/** Fetch the combined RSS + Twitter feed, newest first. */
export async function getFeed(limit = 40): Promise<FeedItem[]> {
  const [articles, tweets] = await Promise.all([
    fetchJson<ApiArticle[]>(`/api/news/?limit=${limit}&hours=168`),
    fetchJson<ApiTwitterPost[]>(`/api/twitter/?limit=${limit}`),
  ]);

  const items = [
    ...(articles ?? []).map(articleToFeedItem),
    ...(tweets ?? []).map(tweetToFeedItem),
  ];

  return items.sort((a, b) => b.sortTime - a.sortTime);
}

/** Fetch a single RSS article by id (used by /article/[id]). Tweets don't
 * have a local detail page - they link out to X directly. */
export async function getArticleById(id: string): Promise<ApiArticle | null> {
  const numericId = Number(id);
  if (!Number.isInteger(numericId)) return null;

  // The backend doesn't have a get-by-id endpoint; fetch a wide-enough
  // window and filter client-side rather than adding a new endpoint just
  // for this. Fine at this data volume; revisit if the feed grows large.
  const articles = await fetchJson<ApiArticle[]>(`/api/news/?limit=100&hours=168`);
  return articles?.find((a) => a.id === numericId) ?? null;
}
