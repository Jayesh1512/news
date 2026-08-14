// Site configuration
export const SITE_CONFIG = {
  name: 'The View Island',
  tagline: 'Editorial News & Analysis',
  description: 'Premium editorial news aggregator with in-depth analysis and commentary',
  subscriptionPrice: '€2.50',
} as const;

// Navigation items
export const NAV_ITEMS = [
  { label: 'World', href: '/?category=world' },
  { label: 'Business', href: '/?category=business' },
  { label: 'Lifestyle', href: '/?category=lifestyle' },
] as const;

// Footer links
export const FOOTER_LINKS = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
  { label: 'Contact', href: '/contact' },
] as const;

// Content settings
export const CONTENT_CONFIG = {
  revalidateSeconds: 300, // 5 minutes
  newsHours: 48,
  newsLimit: 10,
  defaultReadTime: '5 min read',
  defaultCommentCount: 38,
} as const;

// Social media links
export const SOCIAL_LINKS = {
  twitter: '#',
  youtube: '#',
  facebook: '#',
  x: '#',
} as const;

// Sidebar content
export const SIDEBAR_CONFIG = {
  trendingAuthor: {
    name: 'Alexa Ruyk',
    initials: 'AR',
  },
  inspirationCard: {
    title: 'Draw Inspiration From Vibrancy',
    readTime: '3 min read',
    comments: 17,
  },
  tideOfThoughts: {
    title: 'Tide of Thoughts',
    description: "Get the View Island Journal's opinion columnists, editors, op-eds, letters for €2.50",
    stats: {
      articles: '2,830 articles',
      authors: '175 authors',
    },
  },
  printEdition: {
    title: 'Get Print Edition',
    description: 'For an authentic tactile experience',
  },
  privacyArticle: {
    title: 'What Happens to Privacy in the New Age of AI',
    comments: 38,
  },
} as const;

// Financial tickers data
export const FINANCIAL_TICKERS = [
  { symbol: 'GHST/USD', value: '5.2%', change: 0.9715, trend: 'up' as const },
  { symbol: 'UMA/USD', value: '3.8%', change: 1.0937, trend: 'up' as const },
  { symbol: 'BRICK/USD', value: '7.1%', change: 0.0772, trend: 'down' as const },
  { symbol: 'LCX/USD', value: '4.4%', change: 0.1570, trend: 'up' as const },
] as const;

// Audio player
export const AUDIO_PLAYER = {
  listeners: '5,810',
  duration: '32:13',
  plays: '98,076',
} as const;
