"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  BarChart3,
  CalendarDays,
  Check,
  ChevronDown,
  ExternalLink,
  FilterX,
  Heart,
  MessageCircle,
  Radio,
  Repeat2,
  Search,
  SlidersHorizontal,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import type { ApiTwitterReply, ApiTwitterThread } from "@/lib/data";

type DatePreset = "all" | "24h" | "7d" | "30d" | "custom";
type SortOption = "latest" | "replies" | "likes" | "views";

type Filters = {
  search: string;
  topic: string;
  author: string;
  language: string;
  datePreset: DatePreset;
  dateFrom: string;
  dateTo: string;
  minLikes: number;
  minViews: number;
  hasReplies: boolean;
  originalOnly: boolean;
  sort: SortOption;
};

const DEFAULT_FILTERS: Filters = {
  search: "",
  topic: "all",
  author: "all",
  language: "all",
  datePreset: "all",
  dateFrom: "",
  dateTo: "",
  minLikes: 0,
  minViews: 0,
  hasReplies: false,
  originalOnly: true,
  sort: "latest",
};

const fieldClassName =
  "h-10 w-full rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary/70 focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50";

function timestamp(value: string | null): number {
  if (!value) return 0;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatTimestamp(value: string | null): string {
  if (!value) return "Unknown date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";
  const month = date.toLocaleString("en", { month: "short", timeZone: "UTC" });
  const day = date.getUTCDate();
  const year = date.getUTCFullYear();
  return `${month} ${day}${year !== new Date().getUTCFullYear() ? `, ${year}` : ""}`;
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", {
    notation: value >= 1_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

function authorInitials(name: string | null, handle: string): string {
  const source = (name || handle).trim();
  const parts = source.split(/\s+/).filter(Boolean);
  return parts
    .slice(0, 2)
    .map((part) => Array.from(part).find((character) => /[\p{L}\p{N}]/u.test(character))?.toUpperCase())
    .filter(Boolean)
    .join("") || "X";
}

function authorHue(handle: string): number {
  return Array.from(handle).reduce((total, char) => total + char.charCodeAt(0), 0) % 360;
}

function Avatar({ name, handle, size = "md" }: { name: string | null; handle: string; size?: "sm" | "md" }) {
  const hue = authorHue(handle);
  return (
    <div
      aria-hidden="true"
      className={`grid shrink-0 place-items-center rounded-full font-semibold text-white shadow-sm ${
        size === "md" ? "size-10 text-xs" : "size-8 text-[0.65rem]"
      }`}
      style={{ backgroundColor: `hsl(${hue} 48% 42%)` }}
    >
      {authorInitials(name, handle)}
    </div>
  );
}

function Metric({ icon: Icon, value, label }: { icon: typeof MessageCircle; value: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground" title={label}>
      <Icon className="size-4" aria-hidden="true" />
      <span className="tabular-nums">{compactNumber(value)}</span>
      <span className="sr-only">{label}</span>
    </span>
  );
}

function Reply({ reply }: { reply: ApiTwitterReply }) {
  return (
    <article className="relative flex gap-3 py-4 first:pt-3">
      <Avatar name={reply.author_name} handle={reply.author} size="sm" />
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center gap-1.5 text-sm">
          <span className="truncate font-semibold text-foreground">
            {reply.author_name || reply.author}
          </span>
          <span className="truncate text-muted-foreground">@{reply.author}</span>
          <span className="text-muted-foreground" aria-hidden="true">·</span>
          <time className="shrink-0 text-xs text-muted-foreground" dateTime={reply.published_at || undefined}>
            {formatTimestamp(reply.published_at)}
          </time>
        </div>
        <p className="mt-1 whitespace-pre-wrap break-words text-[0.94rem] leading-6 text-foreground/95">
          {reply.text}
        </p>
        <div className="mt-3 flex items-center gap-5">
          <Metric icon={Heart} value={reply.likes} label="Likes" />
          <Metric icon={Repeat2} value={reply.retweets} label="Reposts" />
          <a
            href={reply.url}
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            aria-label={`Open reply from ${reply.author} on X`}
          >
            <ExternalLink className="size-3.5" />
          </a>
        </div>
      </div>
    </article>
  );
}

function Post({ thread }: { thread: ApiTwitterThread }) {
  const [expanded, setExpanded] = useState(false);
  const [expandedText, setExpandedText] = useState(false);
  const { post } = thread;
  const isLongPost = post.text.length > 620;
  const visibleText = isLongPost && !expandedText
    ? `${post.text.slice(0, 620).trimEnd()}…`
    : post.text;
  const replies = useMemo(
    () => [...thread.replies].sort((a, b) => timestamp(a.published_at) - timestamp(b.published_at)),
    [thread.replies],
  );

  return (
    <article className="border-b px-4 py-5 transition-colors hover:bg-muted/20 sm:px-5">
      <div className="flex gap-3">
        <Avatar name={post.author_name} handle={post.author} />
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-center gap-1.5 text-sm">
            <span className="truncate font-semibold text-foreground">
              {post.author_name || post.author}
            </span>
            <span className="truncate text-muted-foreground">@{post.author}</span>
            <span className="text-muted-foreground" aria-hidden="true">·</span>
            <time className="shrink-0 text-xs text-muted-foreground" dateTime={post.published_at || undefined}>
              {formatTimestamp(post.published_at)}
            </time>
            <a
              href={post.url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              aria-label={`Open post from ${post.author} on X`}
            >
              <ExternalLink className="size-3.5" />
            </a>
          </div>

          <p className="mt-1.5 whitespace-pre-wrap break-words text-[0.98rem] leading-6 text-foreground">
            {visibleText}
          </p>

          {isLongPost && (
            <button
              type="button"
              onClick={() => setExpandedText((value) => !value)}
              className="mt-1 rounded-md py-1 text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
              {expandedText ? "Show less" : "Show more"}
            </button>
          )}

          <div className="mt-4 flex max-w-md items-center justify-between gap-3">
            <Metric icon={MessageCircle} value={replies.length || post.replies} label="Replies" />
            <Metric icon={Repeat2} value={post.retweets} label="Reposts" />
            <Metric icon={Heart} value={post.likes} label="Likes" />
            <Metric icon={BarChart3} value={post.views} label="Views" />
          </div>

          {replies.length > 0 && (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              aria-expanded={expanded}
              className="mt-4 inline-flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-primary transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
              <MessageCircle className="size-4" aria-hidden="true" />
              {expanded ? "Hide conversation" : `View conversation · ${replies.length}`}
              <ChevronDown
                className={`size-4 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
                aria-hidden="true"
              />
            </button>
          )}

          {expanded && replies.length > 0 && (
            <div className="relative mt-3 border-t pl-1">
              <div className="absolute bottom-5 left-4.5 top-5 w-px bg-border" aria-hidden="true" />
              <div className="divide-y pl-0.5">
                {replies.map((reply) => (
                  <Reply key={reply.reply_id} reply={reply} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function FilterPanel({
  filters,
  setFilters,
  topics,
  authors,
  languages,
  resultCount,
}: {
  filters: Filters;
  setFilters: (filters: Filters) => void;
  topics: string[];
  authors: string[];
  languages: string[];
  resultCount: number;
}) {
  const update = <Key extends keyof Filters>(key: Key, value: Filters[Key]) => {
    setFilters({ ...filters, [key]: value });
  };

  const isDefault = JSON.stringify(filters) === JSON.stringify(DEFAULT_FILTERS);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Filters</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {resultCount} {resultCount === 1 ? "conversation" : "conversations"}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          disabled={isDefault}
          onClick={() => setFilters(DEFAULT_FILTERS)}
        >
          <FilterX aria-hidden="true" />
          Reset
        </Button>
      </div>

      <div className="space-y-2">
        <label htmlFor="x-filter-search" className="text-xs font-semibold text-muted-foreground">
          Search conversations
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <input
            id="x-filter-search"
            value={filters.search}
            onChange={(event) => update("search", event.target.value)}
            placeholder="Keywords, author, reply…"
            className={`${fieldClassName} pl-9`}
          />
        </div>
      </div>

      <fieldset className="space-y-2">
        <legend className="text-xs font-semibold text-muted-foreground">Date posted</legend>
        <div className="grid grid-cols-2 gap-2">
          {([
            ["all", "All time"],
            ["24h", "Past 24h"],
            ["7d", "Past 7 days"],
            ["30d", "Past 30 days"],
          ] as const).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => update("datePreset", value)}
              className={`flex h-9 items-center justify-center gap-1.5 rounded-lg border px-2 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 ${
                filters.datePreset === value
                  ? "border-primary/40 bg-primary/12 text-primary"
                  : "border-input bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {filters.datePreset === value && <Check className="size-3" aria-hidden="true" />}
              {label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => update("datePreset", "custom")}
          className={`flex h-9 w-full items-center justify-center gap-2 rounded-lg border text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 ${
            filters.datePreset === "custom"
              ? "border-primary/40 bg-primary/12 text-primary"
              : "border-input text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          <CalendarDays className="size-3.5" aria-hidden="true" />
          Custom range
        </button>
        {filters.datePreset === "custom" && (
          <div className="grid grid-cols-2 gap-2 pt-1">
            <label className="space-y-1 text-[0.68rem] text-muted-foreground">
              From
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(event) => update("dateFrom", event.target.value)}
                className={fieldClassName}
              />
            </label>
            <label className="space-y-1 text-[0.68rem] text-muted-foreground">
              To
              <input
                type="date"
                value={filters.dateTo}
                onChange={(event) => update("dateTo", event.target.value)}
                className={fieldClassName}
              />
            </label>
          </div>
        )}
      </fieldset>

      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Topic
          <select value={filters.topic} onChange={(event) => update("topic", event.target.value)} className={fieldClassName}>
            <option value="all">All topics</option>
            {topics.map((topic) => <option key={topic} value={topic}>{topic}</option>)}
          </select>
        </label>
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Language
          <select value={filters.language} onChange={(event) => update("language", event.target.value)} className={fieldClassName}>
            <option value="all">All</option>
            {languages.map((language) => <option key={language} value={language}>{language.toUpperCase()}</option>)}
          </select>
        </label>
      </div>

      <label className="space-y-2 text-xs font-semibold text-muted-foreground">
        Author
        <select value={filters.author} onChange={(event) => update("author", event.target.value)} className={fieldClassName}>
          <option value="all">All authors</option>
          {authors.map((author) => <option key={author} value={author}>@{author}</option>)}
        </select>
      </label>

      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Min. likes
          <input
            type="number"
            min="0"
            value={filters.minLikes}
            onChange={(event) => update("minLikes", Math.max(0, Number(event.target.value) || 0))}
            className={fieldClassName}
          />
        </label>
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Min. views
          <input
            type="number"
            min="0"
            value={filters.minViews}
            onChange={(event) => update("minViews", Math.max(0, Number(event.target.value) || 0))}
            className={fieldClassName}
          />
        </label>
      </div>

      <fieldset className="space-y-3 border-y py-4">
        <legend className="sr-only">Post criteria</legend>
        <label className="flex cursor-pointer items-center justify-between gap-3 text-sm">
          <span>
            <span className="block font-medium">Has conversation</span>
            <span className="text-xs text-muted-foreground">Only posts with fetched replies</span>
          </span>
          <input
            type="checkbox"
            checked={filters.hasReplies}
            onChange={(event) => update("hasReplies", event.target.checked)}
            className="size-4 accent-primary"
          />
        </label>
        <label className="flex cursor-pointer items-center justify-between gap-3 text-sm">
          <span>
            <span className="block font-medium">Original posts only</span>
            <span className="text-xs text-muted-foreground">Hide reposts from results</span>
          </span>
          <input
            type="checkbox"
            checked={filters.originalOnly}
            onChange={(event) => update("originalOnly", event.target.checked)}
            className="size-4 accent-primary"
          />
        </label>
      </fieldset>

      <label className="space-y-2 text-xs font-semibold text-muted-foreground">
        Sort by
        <select value={filters.sort} onChange={(event) => update("sort", event.target.value as SortOption)} className={fieldClassName}>
          <option value="latest">Latest posted</option>
          <option value="replies">Most discussed</option>
          <option value="likes">Most liked</option>
          <option value="views">Most viewed</option>
        </select>
      </label>
    </div>
  );
}

function filterThreads(threads: ApiTwitterThread[], filters: Filters): ApiTwitterThread[] {
  const now = Date.now();
  const presetCutoff =
    filters.datePreset === "24h" ? now - 86_400_000
      : filters.datePreset === "7d" ? now - 7 * 86_400_000
        : filters.datePreset === "30d" ? now - 30 * 86_400_000
          : 0;
  const customFrom = filters.dateFrom ? Date.parse(`${filters.dateFrom}T00:00:00Z`) : 0;
  const customTo = filters.dateTo ? Date.parse(`${filters.dateTo}T23:59:59Z`) : Number.POSITIVE_INFINITY;
  const needle = filters.search.trim().toLocaleLowerCase();

  const filtered = threads.filter(({ post, replies }) => {
    const postedAt = timestamp(post.published_at);
    const searchable = [
      post.text,
      post.author,
      post.author_name || "",
      ...replies.flatMap((reply) => [reply.text, reply.author, reply.author_name || ""]),
    ].join(" ").toLocaleLowerCase();

    if (needle && !searchable.includes(needle)) return false;
    if (filters.topic !== "all" && post.search_query !== filters.topic) return false;
    if (filters.author !== "all" && post.author !== filters.author) return false;
    if (filters.language !== "all" && post.lang !== filters.language) return false;
    if (filters.datePreset !== "all" && filters.datePreset !== "custom" && postedAt < presetCutoff) return false;
    if (filters.datePreset === "custom" && (postedAt < customFrom || postedAt > customTo)) return false;
    if (post.likes < filters.minLikes || post.views < filters.minViews) return false;
    if (filters.hasReplies && replies.length === 0) return false;
    if (filters.originalOnly && post.is_retweet) return false;
    return true;
  });

  return filtered.sort((a, b) => {
    if (filters.sort === "replies") return b.replies.length - a.replies.length;
    if (filters.sort === "likes") return b.post.likes - a.post.likes;
    if (filters.sort === "views") return b.post.views - a.post.views;
    return timestamp(b.post.published_at) - timestamp(a.post.published_at);
  });
}

export function XTimeline({ threads }: { threads: ApiTwitterThread[] }) {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const topics = useMemo(
    () => Array.from(new Set(threads.map(({ post }) => post.search_query).filter((value): value is string => Boolean(value)))).sort(),
    [threads],
  );
  const authors = useMemo(
    () => Array.from(new Set(threads.map(({ post }) => post.author))).sort((a, b) => a.localeCompare(b)),
    [threads],
  );
  const languages = useMemo(
    () => Array.from(new Set(threads.map(({ post }) => post.lang).filter((value): value is string => Boolean(value)))).sort(),
    [threads],
  );
  const filteredThreads = useMemo(() => filterThreads(threads, filters), [threads, filters]);
  const participantCount = useMemo(
    () => new Set(threads.flatMap(({ replies }) => replies.map((reply) => reply.author))).size,
    [threads],
  );
  const activeFilterCount = [
    filters.search,
    filters.topic !== "all",
    filters.author !== "all",
    filters.language !== "all",
    filters.datePreset !== "all",
    filters.minLikes > 0,
    filters.minViews > 0,
    filters.hasReplies,
    !filters.originalOnly,
    filters.sort !== "latest",
  ].filter(Boolean).length;

  const panelProps = { filters, setFilters, topics, authors, languages, resultCount: filteredThreads.length };

  return (
    <div className="mx-auto grid h-[calc(100dvh-3.5rem)] w-full max-w-6xl grid-cols-1 overflow-hidden border-x lg:grid-cols-[minmax(0,1fr)_20rem]">
      <main className="x-scrollbar min-w-0 overflow-y-auto border-r" aria-label="X conversation timeline">
        <div className="sticky top-0 z-20 border-b bg-background/92 px-4 py-3 backdrop-blur-md sm:px-5">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold tracking-tight">X Pulse</h1>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/12 px-2 py-1 text-[0.68rem] font-semibold text-primary">
                  <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
                  Topic feed
                </span>
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {topics.length === 1 ? topics[0] : `${topics.length} tracked topics`} · {threads.length} posts · {participantCount} participants
              </p>
            </div>

            <Sheet>
              <SheetTrigger render={<Button variant="outline" size="sm" className="lg:hidden" />}>
                <SlidersHorizontal aria-hidden="true" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="grid size-5 place-items-center rounded-full bg-primary text-[0.65rem] text-primary-foreground">
                    {activeFilterCount}
                  </span>
                )}
              </SheetTrigger>
              <SheetContent className="w-[min(90vw,24rem)] overflow-y-auto">
                <SheetHeader className="border-b">
                  <SheetTitle>Filter X Pulse</SheetTitle>
                  <SheetDescription>Refine the stored topic conversations.</SheetDescription>
                </SheetHeader>
                <div className="px-4 pb-8">
                  <FilterPanel {...panelProps} />
                </div>
              </SheetContent>
            </Sheet>
          </div>
          <nav className="-mx-4 -mb-3 mt-3 grid grid-cols-2 border-t sm:-mx-5" aria-label="X Pulse sections">
            <Link
              href="/x"
              aria-current="page"
              className="relative flex h-10 items-center justify-center text-sm font-semibold text-foreground after:absolute after:inset-x-[30%] after:bottom-0 after:h-0.5 after:rounded-full after:bg-primary"
            >
              Posts
            </Link>
            <Link
              href="/x/profiles"
              className="flex h-10 items-center justify-center text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary/50"
            >
              People
            </Link>
          </nav>
        </div>

        {filteredThreads.length > 0 ? (
          <div>
            {filteredThreads.map((thread) => (
              <Post key={thread.post.tweet_id} thread={thread} />
            ))}
          </div>
        ) : (
          <div className="grid min-h-[60vh] place-items-center px-6 py-16 text-center">
            <div className="max-w-sm">
              <div className="mx-auto grid size-12 place-items-center rounded-full bg-muted text-muted-foreground">
                {threads.length === 0 ? <Radio className="size-5" /> : <FilterX className="size-5" />}
              </div>
              <h2 className="mt-4 text-base font-semibold">
                {threads.length === 0 ? "No X conversations yet" : "No conversations match"}
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {threads.length === 0
                  ? "Run the configured X topic scraper, then refresh this page."
                  : "Broaden the date range or remove one of the active filters."}
              </p>
              {threads.length > 0 && (
                <Button className="mt-5" variant="outline" onClick={() => setFilters(DEFAULT_FILTERS)}>
                  Clear all filters
                </Button>
              )}
            </div>
          </div>
        )}
      </main>

      <aside className="x-scrollbar hidden overflow-y-auto bg-sidebar/35 lg:block" aria-label="Timeline filters">
        <div className="p-5">
          <FilterPanel {...panelProps} />
          <div className="mt-7 border-t pt-5">
            <div className="flex items-start gap-3 text-xs leading-5 text-muted-foreground">
              <Users className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <p>
                Filters run locally against stored posts and fetched replies. Open a conversation to inspect every captured participant.
              </p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
