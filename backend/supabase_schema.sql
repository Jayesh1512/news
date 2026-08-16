-- Supabase schema for storing scraped Twitter/X posts.
--
-- Run this once in the Supabase SQL editor (or `supabase db execute` /
-- psql against the project's Postgres connection string) before starting
-- the scrape_twitter_accounts Celery job. Table name matches
-- SUPABASE_TWITTER_TABLE in backend/.env (default: twitter_posts).

create table if not exists public.twitter_posts (
    tweet_id            text primary key,
    account             text not null,        -- handle we scraped from (app.core.constants.TWITTER_ACCOUNTS)
    author              text not null,        -- actual author's handle (differs from `account` on retweets)
    author_name         text,
    text                text not null,
    url                 text not null,
    is_retweet          boolean not null default false,
    lang                text,
    likes               integer not null default 0,
    retweets            integer not null default 0,
    replies             integer not null default 0,
    views               integer not null default 0,
    media_url           text,
    published_at        timestamptz,
    fetched_at          timestamptz not null default now(),
    raw                 jsonb                 -- full twitter-cli tweet object, for anything not modeled above
);

create index if not exists idx_twitter_posts_account_published
    on public.twitter_posts (account, published_at desc);

create index if not exists idx_twitter_posts_fetched_at
    on public.twitter_posts (fetched_at desc);

-- Row Level Security: locked down by default. The backend writes with the
-- service_role key (which bypasses RLS), so no policies are strictly
-- required for the scraper to work. Add a read-only policy if you want to
-- query this table from a client using the anon/public key instead.
alter table public.twitter_posts enable row level security;

-- Example read-only policy for the anon key (uncomment if needed):
-- create policy "Public read access" on public.twitter_posts
--     for select using (true);
