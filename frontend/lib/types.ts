export interface Article {
  id: number;
  title: string;
  content: string | null;
  url: string;
  source: string;
  author: string | null;
  published_at: string | null;
  fetched_at: string;
  category: string | null;
  image_url: string | null;
}

export interface NewsStats {
  total_articles: number;
  recent_24h: number;
  by_source: Record<string, number>;
}

export interface Source {
  id: number;
  name: string;
  platform: string;
  url: string | null;
  is_active: boolean;
  last_scraped_at: string | null;
  created_at: string;
}
