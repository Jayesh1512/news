import { Article } from '@/lib/types';
import Link from 'next/link';

interface CompactArticleProps {
  article: Article;
}

export function CompactArticle({ article }: CompactArticleProps) {
  const publishedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : new Date(article.fetched_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <article className="group">
      <Link href={article.url} target="_blank" rel="noopener noreferrer" className="block">
        {/* Image */}
        <div className="aspect-[16/10] bg-editorial-cream-dark rounded overflow-hidden mb-4">
          {article.image_url ? (
            <img
              src={article.image_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-editorial-cream to-editorial-cream-dark" />
          )}
        </div>

        {/* Meta */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-editorial-warm-gray">
            <span>{article.author || 'Editorial'}</span>
            <span>•</span>
            <span>{publishedDate}</span>
          </div>

          <h3 className="font-display text-2xl leading-snug hover:text-editorial-warm-gray transition-colors">
            {article.title}
          </h3>

          <p className="text-editorial-warm-gray text-sm line-clamp-3">
            {article.content || 'Explore this story to learn more about the latest developments.'}
          </p>

          <div className="flex items-center gap-3 text-xs text-editorial-warm-gray">
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>17</span>
            </div>
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>3 min read</span>
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
}
