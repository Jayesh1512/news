import { searchNews } from '@/lib/api-client';
import { NewsGrid } from '@/components/news-grid';
import { SearchBar } from '@/components/search-bar';
import Link from 'next/link';

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const query = searchParams.q || '';
  const articles = query ? await searchNews(query, 50) : [];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 hover:text-blue-600 dark:hover:text-blue-400"
              >
                ← News Aggregator
              </Link>
            </div>
            <SearchBar />
            {query && (
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Search results for: <strong>{query}</strong>
              </p>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <NewsGrid articles={articles} />
      </main>
    </div>
  );
}
