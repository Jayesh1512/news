// Real news data: reads RSS articles from Supabase (see app/lib/data.ts,
// which also backs the public app/api/news Route Handler) and normalizes
// them into the feed. Server Components call the data layer directly rather
// than fetching this app's own Route Handlers - see Next.js docs, "Server
// Components" caveat under Route Handlers: an extra HTTP round trip and it
// fails at build time for prerendered routes since there's no server
// listening yet.
//
// Twitter/X posts (app/lib/data.ts's getTwitterPosts, backing app/api/twitter)
// are intentionally NOT merged into this feed right now. The plan is to pull
// tweets, transform/rewrite them, and insert the results into the `articles`
// table upstream (backend job) so they show up here like any other article -
// see repo notes for that pipeline. Once that exists, getFeed can go back to
// being articles-only forever, so no tweet-merging code is needed here.
import { getArticles, getArticleByIdCached, type ApiArticle } from "@/lib/data";

export const categories = [
  "Home",
  "World",
  "Business",
  "Technology",
  "Sports",
  "Science",
  "Culture",
] as const;

/** Feed item shown in the UI, backed by an `articles` row. */
export type FeedItem = {
  id: string;
  kind: "article";
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

/** Fetch the articles feed, newest first. */
export async function getFeed(limit = 40): Promise<FeedItem[]> {
  const articles = await getArticles({ limit, hours: 168 });
  return articles.map(articleToFeedItem).sort((a, b) => b.sortTime - a.sortTime);
}

/** Fetch a single RSS article by id (used by /article/[id]). */
export async function getArticleById(id: string): Promise<ApiArticle | null> {
  const numericId = Number(id);
  if (!Number.isInteger(numericId)) return null;
  return getArticleByIdCached(numericId);
}
