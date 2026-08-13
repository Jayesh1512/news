import { Article } from '@/lib/types';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const publishedDate = article.published_at
    ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true })
    : formatDistanceToNow(new Date(article.fetched_at), { addSuffix: true });

  return (
    <article className="flex flex-col gap-3 p-4 border rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-zinc-900 dark:border-zinc-800">
      {article.image_url && (
        <div className="w-full h-48 bg-zinc-100 dark:bg-zinc-800 rounded overflow-hidden">
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}
      
      <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
        <span className="px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded text-xs font-medium">
          {article.source}
        </span>
        {article.category && (
          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded text-xs font-medium">
            {article.category}
          </span>
        )}
        <span className="ml-auto text-xs">{publishedDate}</span>
      </div>

      <h2 className="text-xl font-semibold leading-snug line-clamp-2 hover:text-blue-600 dark:hover:text-blue-400">
        <Link href={article.url} target="_blank" rel="noopener noreferrer">
          {article.title}
        </Link>
      </h2>

      {article.content && (
        <p className="text-zinc-600 dark:text-zinc-400 line-clamp-3 text-sm">
          {article.content}
        </p>
      )}

      {article.author && (
        <p className="text-xs text-zinc-500 dark:text-zinc-500">
          By {article.author}
        </p>
      )}

      <Link
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-blue-600 dark:text-blue-400 hover:underline mt-auto"
      >
        Read full article →
      </Link>
    </article>
  );
}
