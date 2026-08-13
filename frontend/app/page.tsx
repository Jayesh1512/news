import { getNews, getNewsStats } from '@/lib/api-client';
import { NewsGrid } from '@/components/news-grid';
import { SearchBar } from '@/components/search-bar';
import Link from 'next/link';

export const revalidate = 300; // Revalidate every 5 minutes

export default async function Home({
  searchParams,
}: {
  searchParams: { source?: string; category?: string };
}) {
  const articles = await getNews({
    source: searchParams.source,
    category: searchParams.category,
    limit: 30,
    hours: 48,
  });

  let stats;
  try {
    stats = await getNewsStats();
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    stats = null;
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      {/* Header */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
                📰 News Aggregator
              </h1>
              <Link
                href="/stats"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                View Stats
              </Link>
            </div>
            <SearchBar />

            {/* Filters */}
            <div className="flex gap-2 flex-wrap">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-full text-sm border transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 border-zinc-300 dark:border-zinc-700"
              >
                All
              </Link>
              <Link
                href="/?source=rss"
                className="px-3 py-1.5 rounded-full text-sm border transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 border-zinc-300 dark:border-zinc-700"
              >
                RSS Feeds
              </Link>
              <Link
                href="/?source=twitter"
                className="px-3 py-1.5 rounded-full text-sm border transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 border-zinc-300 dark:border-zinc-700"
              >
                Twitter
              </Link>
              <Link
                href="/?category=technology"
                className="px-3 py-1.5 rounded-full text-sm border transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 border-zinc-300 dark:border-zinc-700"
              >
                Technology
              </Link>
              <Link
                href="/?category=general"
                className="px-3 py-1.5 rounded-full text-sm border transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800 border-zinc-300 dark:border-zinc-700"
              >
                General
              </Link>
            </div>

            {stats && (
              <div className="text-sm text-zinc-600 dark:text-zinc-400">
                {stats.total_articles} articles • {stats.recent_24h} in last 24h
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <NewsGrid articles={articles} />
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 mt-20">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-zinc-600 dark:text-zinc-400">
          News Aggregator • Built with Next.js and FastAPI
        </div>
      </footer>
    </div>
  );
}
