import Link from 'next/link';
import { NAV_ITEMS, SITE_CONFIG, AUDIO_PLAYER } from '@/lib/constants';

export function Header() {
  return (
    <header className="border-b border-editorial bg-editorial-cream">
      <div className="max-w-[1400px] mx-auto px-6">
        <div className="flex items-center justify-between py-4">
          {/* Left: Audio Player */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18V5l12-2v13M9 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm12-2c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2z"/>
              </svg>
              <span className="font-medium">{AUDIO_PLAYER.listeners}</span>
            </div>
            <button className="w-10 h-10 rounded-full bg-editorial-charcoal text-white flex items-center justify-center hover:bg-editorial-charcoal-light transition-colors">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
            </button>
          </div>

          {/* Center: Navigation */}
          <nav className="flex items-center gap-8">
            {NAV_ITEMS.map((item) => (
              <Link 
                key={item.href}
                href={item.href} 
                className="text-sm text-editorial-charcoal hover:text-editorial-warm-gray transition-colors"
              >
                {item.label} <span className="ml-1">▾</span>
              </Link>
            ))}
          </nav>

          {/* Right: Subscribe + Menu */}
          <div className="flex items-center gap-4">
            <Link 
              href="/subscribe" 
              className="px-4 py-2 border border-editorial-charcoal rounded-full text-sm font-medium text-editorial-charcoal hover:bg-editorial-charcoal hover:text-white transition-colors flex items-center gap-2"
            >
              Subscribe for {SITE_CONFIG.subscriptionPrice}
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M7 17L17 7M17 7H7M17 7v10"/>
              </svg>
            </Link>
            <button className="p-2 hover:bg-editorial-cream-dark rounded transition-colors">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export function Logo() {
  return (
    <div className="text-center py-8 border-b border-editorial">
      <Link href="/" className="inline-block">
        <h1 className="font-display text-5xl tracking-tight">
          THE<span className="font-bold">VIEW</span>ISLAND
        </h1>
      </Link>
    </div>
  );
}
