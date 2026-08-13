import { getNewsStats, getSources } from '@/lib/api-client';
import Link from 'next/link';

export const revalidate = 600; // Revalidate every 10 minutes

export default async function StatsPage() {
  const stats = await getNewsStats();
  const sources = await getSources();

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 hover:text-blue-600 dark:hover:text-blue-400"
            >
              ← News Aggregator
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 text-zinc-900 dark:text-zinc-50">
          Statistics
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
              Total Articles
            </p>
            <p className="text-4xl font-bold text-zinc-900 dark:text-zinc-50">
              {stats.total_articles}
            </p>
          </div>

          <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
              Last 24 Hours
            </p>
            <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
              {stats.recent_24h}
            </p>
          </div>

          <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg">
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-2">
              Active Sources
            </p>
            <p className="text-4xl font-bold text-green-600 dark:text-green-400">
              {sources.filter((s) => s.is_active).length}
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-zinc-900 dark:text-zinc-50">
            Articles by Source
          </h2>
          <div className="space-y-3">
            {Object.entries(stats.by_source).map(([source, count]) => (
              <div key={source} className="flex items-center justify-between">
                <span className="font-medium capitalize text-zinc-900 dark:text-zinc-50">
                  {source}
                </span>
                <span className="text-zinc-600 dark:text-zinc-400">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-zinc-900 dark:text-zinc-50">
            Configured Sources
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800">
                  <th className="text-left py-3 px-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Name
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Platform
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                    Last Scraped
                  </th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr
                    key={source.id}
                    className="border-b border-zinc-100 dark:border-zinc-800/50"
                  >
                    <td className="py-3 px-4 text-zinc-900 dark:text-zinc-50">
                      {source.name}
                    </td>
                    <td className="py-3 px-4 text-zinc-600 dark:text-zinc-400">
                      {source.platform}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          source.is_active
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                        }`}
                      >
                        {source.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-zinc-600 dark:text-zinc-400">
                      {source.last_scraped_at
                        ? new Date(source.last_scraped_at).toLocaleString()
                        : 'Never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
