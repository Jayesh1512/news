import { getNews } from '@/lib/api-client';
import { getMockArticles } from '@/lib/mock-data';
import { Header, Logo } from '@/components/header';
import { HeroArticle } from '@/components/hero-article';
import { CompactArticle } from '@/components/compact-article';
import { Sidebar } from '@/components/sidebar';
import { CONTENT_CONFIG, SITE_CONFIG, FOOTER_LINKS } from '@/lib/constants';

export const revalidate = CONTENT_CONFIG.revalidateSeconds;

export default async function Home() {
  let articles;
  
  try {
    articles = await getNews({
      limit: CONTENT_CONFIG.newsLimit,
      hours: CONTENT_CONFIG.newsHours,
    });
    
    // If no articles from API, use mock data
    if (!articles || articles.length === 0) {
      articles = getMockArticles(CONTENT_CONFIG.newsLimit);
    }
  } catch (error) {
    console.log('Using mock data (backend unavailable)');
    articles = getMockArticles(CONTENT_CONFIG.newsLimit);
  }

  // Split articles for layout
  const heroArticle = articles[0];
  const columnArticles = articles.slice(1, 3);
  const sidebarArticles = articles.slice(3, 10);

  return (
    <div className="min-h-screen bg-editorial-cream">
      <Header />
      <Logo />

      {/* Main Content */}
      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Left Column - Hero Article */}
          <div className="lg:col-span-5">
            {heroArticle && <HeroArticle article={heroArticle} />}
          </div>

          {/* Middle Column - Two Articles */}
          <div className="lg:col-span-4 space-y-12">
            {columnArticles.map((article) => (
              <CompactArticle key={article.id} article={article} />
            ))}
          </div>

          {/* Right Sidebar */}
          <div className="lg:col-span-3">
            <Sidebar trendingArticles={sidebarArticles} />
          </div>
        </div>

        {/* Bottom Featured Article */}
        {articles[3] && (
          <div className="mt-16 border-t pt-12">
            <div className="max-w-4xl">
              <div className="bg-editorial-charcoal text-white rounded-lg p-8 flex items-center gap-6">
                <div className="flex-1">
                  <h3 className="font-display text-2xl mb-2">
                    What Happens to Privacy in the New Age of AI
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-editorial-muted">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    <span>{CONTENT_CONFIG.defaultCommentCount}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-editorial mt-20">
        <div className="max-w-[1400px] mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-editorial-warm-gray">
            <p>© 2024 {SITE_CONFIG.name}. All rights reserved.</p>
            <nav className="flex gap-6">
              {FOOTER_LINKS.map((link) => (
                <a 
                  key={link.href}
                  href={link.href} 
                  className="hover:text-editorial-charcoal transition-colors"
                >
                  {link.label}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
