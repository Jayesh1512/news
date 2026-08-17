// Real news data: reads RSS articles and Twitter/X posts from Supabase (see
// app/lib/data.ts, which also backs the public app/api/news and
// app/api/twitter Route Handlers) and normalizes them into a single feed.
// Server Components call the data layer directly rather than fetching this
// app's own Route Handlers - see Next.js docs, "Server Components" caveat
// under Route Handlers: an extra HTTP round trip and it fails at build time
// for prerendered routes since there's no server listening yet.
import { getArticles, getArticleByIdCached, getTwitterPosts, type ApiArticle, type ApiTwitterPost } from "@/lib/data";

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

/** Fetch the combined RSS + Twitter feed, newest first. */
export async function getFeed(limit = 40): Promise<FeedItem[]> {
  const [articles, tweets] = await Promise.all([
    getArticles({ limit, hours: 168 }),
    getTwitterPosts({ limit }),
  ]);

  const items = [
    ...articles.map(articleToFeedItem),
    ...tweets.map(tweetToFeedItem),
  ];

  return items.sort((a, b) => b.sortTime - a.sortTime);
}

/** Fetch a single RSS article by id (used by /article/[id]). Tweets don't
 * have a local detail page - they link out to X directly. */
export async function getArticleById(id: string): Promise<ApiArticle | null> {
  const numericId = Number(id);
  if (!Number.isInteger(numericId)) return null;
  return getArticleByIdCached(numericId);
}
