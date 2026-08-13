import { Article } from '@/lib/types';
import { ArticleCard } from './article-card';

interface NewsGridProps {
  articles: Article[];
}

export function NewsGrid({ articles }: NewsGridProps) {
  if (articles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <p className="text-xl text-zinc-600 dark:text-zinc-400">No articles found</p>
        <p className="text-sm text-zinc-500 dark:text-zinc-500 mt-2">
          Articles will appear here once the scraper runs
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {articles.map((article) => (
        <ArticleCard key={article.id} article={article} />
      ))}
    </div>
  );
}
