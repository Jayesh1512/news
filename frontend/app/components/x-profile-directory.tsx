"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  ExternalLink,
  FilterX,
  Heart,
  LoaderCircle,
  MessageCircle,
  Search,
  SlidersHorizontal,
  Sparkles,
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
import type { ApiTwitterProfile, ApiTwitterProfilePost } from "@/lib/data";

type ProfileStatus = "all" | "matched" | "summarized" | "needs-review";
type SortOption = "relevance" | "matches" | "coverage" | "recent";
type DiscoveryPhase = "idle" | "generating" | "queued" | "complete" | "error";

type TopicDiscovery = {
  task_id: string;
  topic: string;
  x_search_query: string;
  context_sentences: string[];
  semantic_context: string;
  context_model: string;
};

type DiscoveryTask = {
  state: string;
  ready: boolean;
  progress?: { phase?: string; current?: number | null; total?: number | null };
  result?: {
    status?: string;
    profile_analysis?: { status?: string; message?: string; profiles_analyzed?: number };
  };
  error?: string;
};

type Filters = {
  search: string;
  topic: string;
  status: ProfileStatus;
  minSimilarity: number;
  minMatchingPosts: number;
  sort: SortOption;
};

const DEFAULT_FILTERS: Filters = {
  search: "",
  topic: "all",
  status: "all",
  minSimilarity: 0,
  minMatchingPosts: 0,
  sort: "relevance",
};

const fieldClassName =
  "h-10 w-full rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary/70 focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50";

function timestamp(value: string | null): number {
  if (!value) return 0;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatDate(value: string | null): string {
  if (!value) return "Unknown date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: date.getUTCFullYear() === new Date().getUTCFullYear() ? undefined : "numeric",
    timeZone: "UTC",
  }).format(date);
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en", {
    notation: value >= 1_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function authorInitials(name: string | null, handle: string): string {
  const parts = (name || handle).trim().split(/\s+/).filter(Boolean);
  return parts
    .slice(0, 2)
    .map((part) => Array.from(part).find((character) => /[\p{L}\p{N}]/u.test(character))?.toUpperCase())
    .filter(Boolean)
    .join("") || "X";
}

function authorHue(handle: string): number {
  return Array.from(handle).reduce((total, character) => total + character.charCodeAt(0), 0) % 360;
}

function Avatar({ name, handle }: { name: string | null; handle: string }) {
  return (
    <div
      aria-hidden="true"
      className="grid size-11 shrink-0 place-items-center rounded-full text-xs font-semibold text-white shadow-sm"
      style={{ backgroundColor: `hsl(${authorHue(handle)} 48% 42%)` }}
    >
      {authorInitials(name, handle)}
    </div>
  );
}

function EvidencePost({ post }: { post: ApiTwitterProfilePost }) {
  return (
    <article className="border-t py-3 first:border-t-0">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className={`font-semibold ${post.matches_topic ? "text-primary" : ""}`}>
          {formatPercent(post.similarity)} match
        </span>
        <span aria-hidden="true">·</span>
        <time dateTime={post.published_at || undefined}>{formatDate(post.published_at)}</time>
        <a
          href={post.url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto rounded-md p-1 transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
          aria-label="Open evidence post on X"
        >
          <ExternalLink className="size-3.5" />
        </a>
      </div>
      <p className="mt-1.5 whitespace-pre-wrap break-words text-sm leading-5 text-foreground/90">
        {post.text}
      </p>
      {post.matched_context && (
        <p className="mt-2 flex gap-1.5 text-xs leading-5 text-muted-foreground">
          <BrainCircuit className="mt-1 size-3 shrink-0 text-primary" aria-hidden="true" />
          <span>Closest context: {post.matched_context}</span>
        </p>
      )}
      <div className="mt-2 flex items-center gap-4 text-[0.7rem] text-muted-foreground">
        <span className="inline-flex items-center gap-1"><MessageCircle className="size-3" />{compactNumber(post.replies)}</span>
        <span className="inline-flex items-center gap-1"><Heart className="size-3" />{compactNumber(post.likes)}</span>
        <span className="inline-flex items-center gap-1"><BarChart3 className="size-3" />{compactNumber(post.views)}</span>
      </div>
    </article>
  );
}

function progressLabel(task: DiscoveryTask | null): string {
  const phase = task?.progress?.phase;
  if (phase === "searching_x") return "Searching X for relevant conversations…";
  if (phase === "fetching_conversations") {
    const current = task?.progress?.current;
    const total = task?.progress?.total;
    return current && total
      ? `Fetching conversations ${current} of ${total}…`
      : "Fetching matching conversations…";
  }
  if (phase === "analyzing_profiles") return "Comparing each profile’s recent posts…";
  if (task?.state === "STARTED") return "Starting the discovery worker…";
  return "Waiting for the discovery worker…";
}

function TopicDiscoveryComposer() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [phase, setPhase] = useState<DiscoveryPhase>("idle");
  const [discovery, setDiscovery] = useState<TopicDiscovery | null>(null);
  const [task, setTask] = useState<DiscoveryTask | null>(null);
  const [error, setError] = useState("");
  const isBusy = phase === "generating" || phase === "queued";

  useEffect(() => {
    if (!discovery || phase !== "queued") return;
    let cancelled = false;

    const checkTask = async () => {
      try {
        const response = await fetch(`/api/twitter/tasks/${discovery.task_id}`, { cache: "no-store" });
        const payload = (await response.json()) as DiscoveryTask & { detail?: string };
        if (!response.ok) throw new Error(payload.detail || "Could not read discovery progress.");
        if (cancelled) return;
        setTask(payload);

        if (payload.state === "FAILURE") {
          setError(payload.error || "Profile discovery failed. Try the topic again.");
          setPhase("error");
        } else if (payload.state === "SUCCESS") {
          if (payload.result?.status !== "success" || payload.result.profile_analysis?.status === "error") {
            setError(
              payload.result?.profile_analysis?.message
                || "The search finished without profile results. Check the configured services and try again.",
            );
            setPhase("error");
          } else {
            setPhase("complete");
            router.refresh();
          }
        }
      } catch (caught) {
        if (cancelled) return;
        setError(caught instanceof Error ? caught.message : "Could not read discovery progress.");
        setPhase("error");
      }
    };

    void checkTask();
    const interval = window.setInterval(checkTask, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [discovery, phase, router]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanTopic = topic.trim();
    if (cleanTopic.length < 2 || isBusy) return;

    setPhase("generating");
    setDiscovery(null);
    setTask(null);
    setError("");
    try {
      const response = await fetch("/api/twitter/topic-searches", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ topic: cleanTopic }),
      });
      const payload = (await response.json()) as TopicDiscovery & { detail?: string };
      if (!response.ok) throw new Error(payload.detail || "Could not start topic discovery.");
      setDiscovery(payload);
      setPhase("queued");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not start topic discovery.");
      setPhase("error");
    }
  };

  return (
    <section className="border-b px-4 py-5 sm:px-5" aria-labelledby="topic-discovery-title">
      <div className="flex gap-3">
        <div className="grid size-11 shrink-0 place-items-center rounded-full bg-foreground text-background">
          <BrainCircuit className="size-5" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 id="topic-discovery-title" className="text-base font-semibold">Find people by topic</h2>
          <p className="mt-1 max-w-[68ch] text-sm leading-5 text-muted-foreground">
            Describe what you care about. AI creates focused context sentences, searches X, then compares them with each person&apos;s recent posts.
          </p>

          <form onSubmit={submit} className="mt-4">
            <label htmlFor="topic-discovery-input" className="sr-only">Topic to search on X</label>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                id="topic-discovery-input"
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                placeholder="e.g. Cheap LLM providers for production apps"
                disabled={isBusy}
                maxLength={160}
                className={`${fieldClassName} h-11 flex-1 rounded-lg`}
              />
              <Button type="submit" className="h-11 shrink-0 rounded-lg px-4" disabled={topic.trim().length < 2 || isBusy}>
                {isBusy ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <Search aria-hidden="true" />}
                {phase === "generating" ? "Building context" : phase === "queued" ? "Searching" : "Generate & search"}
              </Button>
            </div>
          </form>

          <div className="mt-2 min-h-5 text-xs text-muted-foreground" aria-live="polite">
            {phase === "idle" && "We’ll use 5–7 independent semantic anchors for cosine matching."}
            {phase === "generating" && "Generating an X query and semantic context…"}
            {phase === "queued" && progressLabel(task)}
            {phase === "complete" && (
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="size-3.5" aria-hidden="true" />
                Search complete. The profile results are now refreshed.
              </span>
            )}
            {phase === "error" && (
              <span className="inline-flex items-start gap-1.5 font-medium text-destructive">
                <CircleAlert className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                {error}
              </span>
            )}
          </div>

          {discovery && (
            <div className="mt-4 border-t pt-4">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
                <span className="font-semibold text-foreground">X query</span>
                <span className="break-all text-muted-foreground">{discovery.x_search_query}</span>
              </div>
              <ol className="mt-3 space-y-2" aria-label="Generated context sentences">
                {discovery.context_sentences.map((sentence, index) => (
                  <li key={sentence} className="flex gap-2 text-sm leading-5 text-foreground/90">
                    <span className="mt-0.5 grid size-4 shrink-0 place-items-center rounded-full bg-primary/12 text-[0.62rem] font-semibold text-primary">
                      {index + 1}
                    </span>
                    <span>{sentence}</span>
                  </li>
                ))}
              </ol>
              {phase === "complete" && (
                <button
                  type="button"
                  onClick={() => {
                    setTopic("");
                    setDiscovery(null);
                    setTask(null);
                    setPhase("idle");
                  }}
                  className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
                >
                  Start another search <ArrowRight className="size-3.5" aria-hidden="true" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ProfileRow({ profile }: { profile: ApiTwitterProfile }) {
  const [expanded, setExpanded] = useState(false);
  const evidence = profile.matching_posts.length > 0
    ? profile.matching_posts
    : [...profile.recent_posts].sort((a, b) => b.similarity - a.similarity).slice(0, 3);

  return (
    <article className="border-b px-4 py-5 transition-colors hover:bg-muted/20 sm:px-5">
      <div className="flex gap-3">
        <Avatar name={profile.display_name} handle={profile.username} />
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-start gap-2">
            <div className="min-w-0 flex-1">
              <div className="flex min-w-0 items-center gap-1.5">
                <h2 className="truncate text-sm font-semibold text-foreground">
                  {profile.display_name || profile.username}
                </h2>
                {profile.summary && (
                  <CheckCircle2 className="size-3.5 shrink-0 text-primary" aria-label="Summary generated" />
                )}
              </div>
              <p className="truncate text-sm text-muted-foreground">@{profile.username}</p>
            </div>
            <a
              href={profile.profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border px-2.5 text-xs font-medium transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
            >
              View on X
              <ExternalLink className="size-3" />
            </a>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
            <span><strong className="font-semibold text-foreground">{profile.matching_post_count}</strong> of {profile.analyzed_post_count} posts match</span>
            <span><strong className="font-semibold text-foreground">{formatPercent(profile.best_similarity)}</strong> best similarity</span>
            <span>{profile.discovered_from.length} discovery {profile.discovered_from.length === 1 ? "signal" : "signals"}</span>
          </div>

          {profile.summary ? (
            <div className="mt-4">
              <p className="text-[0.95rem] leading-6 text-foreground">{profile.summary.overview}</p>
              <div className="mt-3 border-l-2 border-primary/50 pl-3">
                <p className="text-[0.68rem] font-semibold uppercase tracking-wide text-primary">Connection to topic</p>
                <p className="mt-1 text-sm leading-5 text-muted-foreground">{profile.summary.topic_connection}</p>
              </div>
              {profile.summary.primary_topics.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5" aria-label="Primary topics">
                  {profile.summary.primary_topics.map((topic) => (
                    <span key={topic} className="rounded-md bg-muted px-2 py-1 text-[0.7rem] font-medium text-muted-foreground">
                      {topic}
                    </span>
                  ))}
                </div>
              )}
              {profile.summary.key_signals.length > 0 && (
                <ul className="mt-3 grid gap-1.5 text-xs leading-5 text-muted-foreground sm:grid-cols-2">
                  {profile.summary.key_signals.map((signal) => (
                    <li key={signal} className="flex gap-1.5">
                      <Sparkles className="mt-1 size-3 shrink-0 text-primary" aria-hidden="true" />
                      <span>{signal}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <div className="mt-4 flex gap-2 rounded-lg bg-muted/60 px-3 py-2.5 text-xs leading-5 text-muted-foreground">
              <CircleAlert className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
              <p>
                {profile.fetch_error || profile.analysis_error
                  ? "This profile could not be fully analyzed."
                  : "A grounded profile summary has not been generated yet."}
              </p>
            </div>
          )}

          {evidence.length > 0 && (
            <div className="mt-4">
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                aria-expanded={expanded}
                className="inline-flex items-center gap-1.5 rounded-md py-1 text-sm font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              >
                {expanded ? "Hide evidence" : `View evidence posts · ${evidence.length}`}
                <ChevronDown className={`size-4 transition-transform ${expanded ? "rotate-180" : ""}`} aria-hidden="true" />
              </button>
              {expanded && (
                <div className="mt-2 border-y">
                  {evidence.map((post) => <EvidencePost key={post.tweet_id} post={post} />)}
                </div>
              )}
            </div>
          )}

          <p className="mt-4 text-[0.68rem] text-muted-foreground">
            Analyzed {formatDate(profile.analyzed_at)} · {profile.embedding_model}
            {profile.summary_model ? ` · ${profile.summary_model}` : ""}
          </p>
        </div>
      </div>
    </article>
  );
}

function FilterPanel({
  filters,
  setFilters,
  topics,
  resultCount,
}: {
  filters: Filters;
  setFilters: (filters: Filters) => void;
  topics: string[];
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
          <h2 className="text-base font-semibold">Profile filters</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">{resultCount} {resultCount === 1 ? "person" : "people"}</p>
        </div>
        <Button variant="ghost" size="sm" disabled={isDefault} onClick={() => setFilters(DEFAULT_FILTERS)}>
          <FilterX aria-hidden="true" />
          Reset
        </Button>
      </div>

      <div className="space-y-2">
        <label htmlFor="profile-filter-search" className="text-xs font-semibold text-muted-foreground">Search people</label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <input
            id="profile-filter-search"
            value={filters.search}
            onChange={(event) => update("search", event.target.value)}
            placeholder="Handle, summary, topic…"
            className={`${fieldClassName} pl-9`}
          />
        </div>
      </div>

      {topics.length > 1 && (
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Analyzed topic
          <select value={filters.topic} onChange={(event) => update("topic", event.target.value)} className={fieldClassName}>
            <option value="all">All topics</option>
            {topics.map((topic) => <option key={topic} value={topic}>{topic}</option>)}
          </select>
        </label>
      )}

      <label className="space-y-2 text-xs font-semibold text-muted-foreground">
        Profile status
        <select value={filters.status} onChange={(event) => update("status", event.target.value as ProfileStatus)} className={fieldClassName}>
          <option value="all">All analyzed</option>
          <option value="matched">Has topic matches</option>
          <option value="summarized">Summary generated</option>
          <option value="needs-review">Needs review</option>
        </select>
      </label>

      <div className="grid grid-cols-2 gap-3">
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Min. similarity
          <select value={filters.minSimilarity} onChange={(event) => update("minSimilarity", Number(event.target.value))} className={fieldClassName}>
            <option value={0}>Any</option>
            <option value={0.5}>50%</option>
            <option value={0.6}>60%</option>
            <option value={0.7}>70%</option>
            <option value={0.8}>80%</option>
          </select>
        </label>
        <label className="space-y-2 text-xs font-semibold text-muted-foreground">
          Min. matches
          <input
            type="number"
            min="0"
            max="15"
            value={filters.minMatchingPosts}
            onChange={(event) => update("minMatchingPosts", Math.max(0, Number(event.target.value) || 0))}
            className={fieldClassName}
          />
        </label>
      </div>

      <label className="space-y-2 text-xs font-semibold text-muted-foreground">
        Sort by
        <select value={filters.sort} onChange={(event) => update("sort", event.target.value as SortOption)} className={fieldClassName}>
          <option value="relevance">Best similarity</option>
          <option value="matches">Most matching posts</option>
          <option value="coverage">Highest match coverage</option>
          <option value="recent">Recently analyzed</option>
        </select>
      </label>
    </div>
  );
}

function filterProfiles(profiles: ApiTwitterProfile[], filters: Filters): ApiTwitterProfile[] {
  const needle = filters.search.trim().toLocaleLowerCase();
  const filtered = profiles.filter((profile) => {
    const searchable = [
      profile.username,
      profile.display_name || "",
      profile.topic,
      profile.summary?.overview || "",
      profile.summary?.topic_connection || "",
      ...(profile.summary?.primary_topics || []),
      ...(profile.summary?.key_signals || []),
    ].join(" ").toLocaleLowerCase();

    if (needle && !searchable.includes(needle)) return false;
    if (filters.topic !== "all" && profile.topic !== filters.topic) return false;
    if (filters.status === "matched" && profile.matching_post_count === 0) return false;
    if (filters.status === "summarized" && !profile.summary) return false;
    if (filters.status === "needs-review" && !(profile.fetch_error || profile.analysis_error || profile.summary_error)) return false;
    if (profile.best_similarity < filters.minSimilarity) return false;
    if (profile.matching_post_count < filters.minMatchingPosts) return false;
    return true;
  });

  return filtered.sort((left, right) => {
    if (filters.sort === "matches") return right.matching_post_count - left.matching_post_count || right.best_similarity - left.best_similarity;
    if (filters.sort === "coverage") {
      const leftCoverage = left.analyzed_post_count ? left.matching_post_count / left.analyzed_post_count : 0;
      const rightCoverage = right.analyzed_post_count ? right.matching_post_count / right.analyzed_post_count : 0;
      return rightCoverage - leftCoverage || right.best_similarity - left.best_similarity;
    }
    if (filters.sort === "recent") return timestamp(right.analyzed_at) - timestamp(left.analyzed_at);
    return right.best_similarity - left.best_similarity || right.matching_post_count - left.matching_post_count;
  });
}

export function XProfileDirectory({ profiles }: { profiles: ApiTwitterProfile[] }) {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const topics = useMemo(() => Array.from(new Set(profiles.map((profile) => profile.topic))).sort(), [profiles]);
  const filteredProfiles = useMemo(() => filterProfiles(profiles, filters), [profiles, filters]);
  const matchedCount = useMemo(() => profiles.filter((profile) => profile.matching_post_count > 0).length, [profiles]);
  const summarizedCount = useMemo(() => profiles.filter((profile) => profile.summary).length, [profiles]);
  const activeFilterCount = [
    filters.search,
    filters.topic !== "all",
    filters.status !== "all",
    filters.minSimilarity > 0,
    filters.minMatchingPosts !== 0,
    filters.sort !== "relevance",
  ].filter(Boolean).length;
  const panelProps = { filters, setFilters, topics, resultCount: filteredProfiles.length };

  return (
    <div className="mx-auto grid h-[calc(100dvh-3.5rem)] w-full max-w-6xl grid-cols-1 overflow-hidden border-x lg:grid-cols-[minmax(0,1fr)_20rem]">
      <main className="x-scrollbar min-w-0 overflow-y-auto border-r" aria-label="Topic-matched X profiles">
        <div className="sticky top-0 z-20 border-b bg-background/92 px-4 py-3 backdrop-blur-md sm:px-5">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold tracking-tight">People</h1>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/12 px-2 py-1 text-[0.68rem] font-semibold text-primary">
                  <Sparkles className="size-3" aria-hidden="true" />
                  AI summaries
                </span>
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {topics.length === 1 ? topics[0] : `${topics.length} topics`} · {matchedCount} matched · {summarizedCount} summarized
              </p>
            </div>

            <Sheet>
              <SheetTrigger render={<Button variant="outline" size="sm" className="lg:hidden" />}>
                <SlidersHorizontal aria-hidden="true" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="grid size-5 place-items-center rounded-full bg-primary text-[0.65rem] text-primary-foreground">{activeFilterCount}</span>
                )}
              </SheetTrigger>
              <SheetContent className="w-[min(90vw,24rem)] overflow-y-auto">
                <SheetHeader className="border-b">
                  <SheetTitle>Filter people</SheetTitle>
                  <SheetDescription>Refine profiles by topic relevance and analysis status.</SheetDescription>
                </SheetHeader>
                <div className="px-4 pb-8"><FilterPanel {...panelProps} /></div>
              </SheetContent>
            </Sheet>
          </div>
          <nav className="-mx-4 -mb-3 mt-3 grid grid-cols-2 border-t sm:-mx-5" aria-label="X Pulse sections">
            <Link
              href="/x"
              className="flex h-10 items-center justify-center text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary/50"
            >
              Posts
            </Link>
            <Link
              href="/x/profiles"
              aria-current="page"
              className="relative flex h-10 items-center justify-center text-sm font-semibold text-foreground after:absolute after:inset-x-[30%] after:bottom-0 after:h-0.5 after:rounded-full after:bg-primary"
            >
              People
            </Link>
          </nav>
        </div>

        <TopicDiscoveryComposer />

        {filteredProfiles.length > 0 ? (
          <div>{filteredProfiles.map((profile) => <ProfileRow key={profile.profile_key} profile={profile} />)}</div>
        ) : (
          <div className="grid min-h-[60vh] place-items-center px-6 py-16 text-center">
            <div className="max-w-sm">
              <div className="mx-auto grid size-12 place-items-center rounded-full bg-muted text-muted-foreground">
                {profiles.length === 0 ? <Users className="size-5" /> : <FilterX className="size-5" />}
              </div>
              <h2 className="mt-4 text-base font-semibold">{profiles.length === 0 ? "No analyzed people yet" : "No people match"}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {profiles.length === 0
                  ? "Enter a topic above to find conversations, compare recent posts, and generate profile summaries."
                  : "Lower the similarity threshold or remove one of the active filters."}
              </p>
              {profiles.length > 0 && (
                <Button className="mt-5" variant="outline" onClick={() => setFilters(DEFAULT_FILTERS)}>Clear all filters</Button>
              )}
            </div>
          </div>
        )}
      </main>

      <aside className="x-scrollbar hidden overflow-y-auto bg-sidebar/35 lg:block" aria-label="Profile filters">
        <div className="p-5">
          <FilterPanel {...panelProps} />
          <div className="mt-7 border-t pt-5">
            <div className="flex items-start gap-3 text-xs leading-5 text-muted-foreground">
              <Users className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <p>Profiles are ranked from cosine similarity across each person&apos;s 10–15 latest public posts. Expand evidence before acting on a match.</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
