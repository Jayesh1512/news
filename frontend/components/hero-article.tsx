import { Article } from '@/lib/types';
import Link from 'next/link';
import { CONTENT_CONFIG } from '@/lib/constants';

interface HeroArticleProps {
  article: Article;
}

export function HeroArticle({ article }: HeroArticleProps) {
  const publishedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : new Date(article.fetched_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <article className="relative group">
      {/* Large Hero Image */}
      <Link href={article.url} target="_blank" rel="noopener noreferrer" className="block">
        <div className="aspect-[4/3] bg-editorial-cream-dark rounded-lg overflow-hidden mb-6">
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

        {/* Article Info */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-sm text-editorial-warm-gray">
            <span className="font-medium">{article.author || 'Editorial Team'}</span>
            <span>•</span>
            <span>{publishedDate}</span>
          </div>

          <h2 className="font-display text-5xl leading-tight tracking-tight hover:text-editorial-warm-gray transition-colors">
            Turn Your Devices From <span className="bg-editorial-accent text-white px-2">Distractions</span> Into Time Savers Either
          </h2>

          <p className="text-editorial-charcoal text-lg leading-relaxed max-w-2xl">
            {article.content || "Every January, I usually purge old snail mail, clothes and unwanted knickknacks to start the year anew. This time, I focused on my digital spaces instead."}
          </p>

          <div className="flex items-center gap-4 text-sm text-editorial-warm-gray">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>{CONTENT_CONFIG.defaultCommentCount}</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>7 min read</span>
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
}
