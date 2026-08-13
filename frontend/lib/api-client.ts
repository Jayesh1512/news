import { Article, NewsStats, Source } from './types';

// Server-side (in Docker): use backend:8000
// Client-side (browser): use localhost:8000 or configured URL
const getAPIURL = () => {
  // Server-side: use internal Docker network
  if (typeof window === 'undefined') {
    return process.env.API_URL_SERVER || 'http://backend:8000';
  }
  // Client-side: use public URL
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_URL = getAPIURL();

export interface NewsParams {
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
  hours?: number;
}

export async function getNews(params: NewsParams = {}): Promise<Article[]> {
  const url = new URL(`${API_URL}/api/news`);
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, String(value));
    }
  });

  const res = await fetch(url.toString(), {
    cache: 'no-store',
    next: { revalidate: 300 } // 5 minutes
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch news: ${res.statusText}`);
  }

  return res.json();
}

export async function searchNews(query: string, limit: number = 20): Promise<Article[]> {
  const url = new URL(`${API_URL}/api/news/search`);
  url.searchParams.append('q', query);
  url.searchParams.append('limit', String(limit));

  const res = await fetch(url.toString(), {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to search news: ${res.statusText}`);
  }

  return res.json();
}

export async function getNewsStats(): Promise<NewsStats> {
  const res = await fetch(`${API_URL}/api/news/stats`, {
    cache: 'no-store',
    next: { revalidate: 600 } // 10 minutes
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.statusText}`);
  }

  return res.json();
}

export async function getSources(): Promise<Source[]> {
  const res = await fetch(`${API_URL}/api/sources`, {
    next: { revalidate: 3600 } // 1 hour
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch sources: ${res.statusText}`);
  }

  return res.json();
}
