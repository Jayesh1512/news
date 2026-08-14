import { Article } from '@/lib/types';
import Link from 'next/link';
import { SIDEBAR_CONFIG, SOCIAL_LINKS, FINANCIAL_TICKERS, AUDIO_PLAYER } from '@/lib/constants';

interface SidebarProps {
  trendingArticles: Article[];
}

export function Sidebar({ trendingArticles }: SidebarProps) {
  return (
    <aside className="space-y-8">
      {/* Trending Author */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-editorial-cream-dark flex items-center justify-center text-editorial-charcoal font-medium">
          {SIDEBAR_CONFIG.trendingAuthor.initials}
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-sm">{SIDEBAR_CONFIG.trendingAuthor.name}</h3>
        </div>
        <div className="flex gap-2">
          <button className="w-8 h-8 rounded-full bg-editorial-accent flex items-center justify-center text-white">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M13.397 20.997v-8.196h2.765l.411-3.209h-3.176V7.548c0-.926.258-1.56 1.587-1.56h1.684V3.127A22.336 22.336 0 0 0 14.201 3c-2.444 0-4.122 1.492-4.122 4.231v2.355H7.332v3.209h2.753v8.202h3.312z"/>
            </svg>
          </button>
          <button className="w-8 h-8 rounded-full border border-editorial flex items-center justify-center hover:bg-editorial-cream-dark">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 17L17 7M17 7H7M17 7v10"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Featured Article */}
      {trendingArticles[0] && (
        <article className="group">
          <Link href={trendingArticles[0].url} target="_blank" rel="noopener noreferrer">
            <h3 className="font-display text-3xl leading-tight mb-4 hover:text-editorial-warm-gray transition-colors">
              {trendingArticles[0].title}
            </h3>
            <p className="text-editorial-warm-gray text-sm leading-relaxed mb-4">
              {trendingArticles[0].content?.slice(0, 150) || 'Hours after the Senate passed the measure, the House followed suit. The bill will now go to President Biden.'}...
            </p>
            <p className="text-xs text-editorial-warm-gray">
              {trendingArticles[0].author || 'Editorial'} • 5 min read
            </p>
          </Link>
        </article>
      )}

      {/* Draw Inspiration Card */}
      <div className="bg-editorial-cream-dark rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-center mb-4">
          <svg className="w-16 h-16 text-editorial-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h4 className="font-display text-xl text-center">{SIDEBAR_CONFIG.inspirationCard.title}</h4>
        <div className="flex items-center justify-center gap-3 text-xs text-editorial-warm-gray">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span>{SIDEBAR_CONFIG.inspirationCard.comments}</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>{SIDEBAR_CONFIG.inspirationCard.readTime}</span>
          </div>
        </div>
      </div>

      {/* Tide of Thoughts */}
      <div className="border-t pt-6">
        <h4 className="font-display text-xl mb-4">{SIDEBAR_CONFIG.tideOfThoughts.title}</h4>
        <p className="text-sm text-editorial-charcoal mb-4">
          {SIDEBAR_CONFIG.tideOfThoughts.description}
        </p>
        <div className="flex items-center gap-3 text-xs text-editorial-warm-gray mb-4">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
            <span>{SIDEBAR_CONFIG.tideOfThoughts.stats.articles}</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <span>{SIDEBAR_CONFIG.tideOfThoughts.stats.authors}</span>
          </div>
        </div>

        {/* Social Links */}
        <div className="flex gap-3">
          <a href={SOCIAL_LINKS.twitter} className="w-10 h-10 rounded-full bg-[var(--color-twitter)] flex items-center justify-center text-white hover:bg-[var(--color-twitter-hover)] transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
            </svg>
          </a>
          <a href={SOCIAL_LINKS.youtube} className="w-10 h-10 rounded-full bg-editorial-accent flex items-center justify-center text-white hover:bg-editorial-accent-hover transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
          </a>
          <a href={SOCIAL_LINKS.facebook} className="w-10 h-10 rounded-full bg-[var(--color-facebook)] flex items-center justify-center text-white hover:bg-[var(--color-facebook-hover)] transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
            </svg>
          </a>
          <a href={SOCIAL_LINKS.x} className="w-10 h-10 rounded-full bg-editorial-charcoal flex items-center justify-center text-white hover:bg-editorial-charcoal-light transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </a>
        </div>

        <div className="mt-4 flex gap-4 text-xs text-editorial-warm-gray">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
            </svg>
            <span>{AUDIO_PLAYER.duration}</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="1"/>
              <circle cx="12" cy="5" r="1"/>
              <circle cx="12" cy="19" r="1"/>
            </svg>
            <span>{AUDIO_PLAYER.plays}</span>
          </div>
        </div>
      </div>

      {/* Financial Tickers */}
      <div className="border-t pt-6 space-y-4">
        {FINANCIAL_TICKERS.map((ticker) => (
          <FinancialTicker key={ticker.symbol} {...ticker} />
        ))}
      </div>

      {/* Print Edition CTA */}
      <div className="bg-editorial-charcoal text-white rounded-lg p-6">
        <h4 className="font-display text-xl mb-2">{SIDEBAR_CONFIG.printEdition.title}</h4>
        <p className="text-sm text-editorial-muted mb-4">{SIDEBAR_CONFIG.printEdition.description}</p>
        <button className="w-10 h-10 rounded-full bg-white text-editorial-charcoal flex items-center justify-center hover:bg-editorial-cream transition-colors">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M7 17L17 7M17 7H7M17 7v10"/>
          </svg>
        </button>
      </div>

      {/* Privacy Article */}
      <div className="bg-editorial-charcoal text-white rounded-lg p-6 space-y-3">
        <h4 className="font-display text-lg">{SIDEBAR_CONFIG.privacyArticle.title}</h4>
        <div className="flex items-center gap-2 text-xs text-editorial-muted">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>{SIDEBAR_CONFIG.privacyArticle.comments}</span>
        </div>
      </div>
    </aside>
  );
}

interface FinancialTickerProps {
  symbol: string;
  value: string;
  change: number;
  trend: 'up' | 'down';
}

function FinancialTicker({ symbol, value, change, trend }: FinancialTickerProps) {
  const trendUpBg = 'bg-green-100';
  const trendUpText = 'text-green-600';
  const trendDownBg = 'bg-red-100';
  const trendDownText = 'text-red-600';
  const neutralBg = 'bg-editorial-cream-dark';
  const neutralText = 'text-editorial-warm-gray';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${trend === 'up' ? trendUpBg : trendDownBg}`}>
            <svg className={`w-4 h-4 ${trend === 'up' ? trendUpText : trendDownText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {trend === 'up' ? (
                <polyline points="18 15 12 9 6 15"/>
              ) : (
                <polyline points="6 9 12 15 18 9"/>
              )}
            </svg>
          </div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${trend === 'down' ? trendDownBg : neutralBg}`}>
            <svg className={`w-4 h-4 ${trend === 'down' ? trendDownText : neutralText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${trend === 'up' ? trendUpBg : neutralBg}`}>
            <svg className={`w-4 h-4 ${trend === 'up' ? trendUpText : neutralText}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="18 15 12 9 6 15"/>
            </svg>
          </div>
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xs text-editorial-warm-gray">{symbol}</span>
        <span className="text-sm font-medium">{change}</span>
        <span className={`text-xs ${trend === 'up' ? trendUpText : trendDownText}`}>{value}</span>
      </div>
    </div>
  );
}
