<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

---

# News Aggregator — Agent Guide

Shared by every coding agent (Claude Code, Codex, Cursor, …). `CLAUDE.md` imports this file.

## 0. Mandatory rules (read first, every task)

1. **Read this file in full before writing or changing code.** Re-read the section for the area you touch (backend §4, frontend §5, scraper §6).
2. **Follow the Ponytail skill (`ponytail:ponytail`) for ALL code you write, edit, refactor, or review.** In Claude Code, invoke it with the Skill tool before coding. Other agents: apply the ladder in §2 verbatim. Not optional.
3. **Preserve the architecture in §3.** Do not move responsibilities between layers, add services, or add a second way to do something the repo already does one way. If a task seems to need an architectural change, stop and ask the user first.
4. **Read before you write.** Grep for an existing helper/pattern before creating one. Read the file you are changing and its callers.
5. **Update the docs you invalidate** (this file, `PORTS.md`, `README.md`, `.env.example`) in the same change.

## 1. What this project is

A news aggregator: FastAPI backend scrapes RSS feeds and X/Twitter profiles on a schedule into Supabase; a Next.js frontend renders one merged, newest-first feed.

```
Next.js (8502) ──HTTP──> FastAPI (8501) ──> Supabase (Postgres + REST)
                              │
                   Celery worker + beat ──> Redis (8500)
                              │
              RSS scraper / Twitter scraper (twitter-cli)
```

| Path | Role |
| --- | --- |
| `backend/` | FastAPI app, scrapers, Celery tasks, DB access (Python ≥3.12, `uv`/`pyproject.toml`) |
| `frontend/` | Next.js 16 App Router + React 19 + Tailwind 4 + shadcn/base-ui (`pnpm`) |
| `twitter-scraper/` | Standalone container: Agent-Reach / `twitter-cli` profile fetcher |
| `docker-compose*.yml` | One file per service plus combined `docker-compose.yml` |
| `PORTS.md`, `CONTAINERS.md`, `QUICK_START.md` | Ops docs; ports are 8500+ |

Stray files at repo root (`package.json`, `tsconfig.json`, `next.config.ts`, `eslint.config.mjs`, `postcss.config.mjs`, lockfiles, `start.sh`) are a leftover Next.js scaffold; **the real frontend lives in `frontend/`**. Don't add code at the root.

## 2. Ponytail — how to write code here

You are a lazy senior dev: efficient, not careless. The best code is the code never written. Stop at the first rung that holds:

1. **Does it need to exist?** Speculative need → skip, say so in one line (YAGNI).
2. **Already in this repo?** Reuse the helper/type/pattern (see §7 for what exists).
3. **Stdlib does it?** Use it.
4. **Native platform feature?** CSS over JS, `<input type="date">` over a picker, DB constraint over app code.
5. **Already-installed dependency?** Use it. Never add a dependency for what a few lines do.
6. **One line?** Write one line.
7. **Only then:** the minimum code that works.

Rules:
- No abstractions with one implementation, no factories for one product, no config for a value that never changes, no scaffolding "for later".
- Deletion over addition. Fewest files, shortest correct diff.
- **Bug fix = root cause.** Grep every caller before editing; fix once in the shared function, not in each caller.
- Mark deliberate corner-cutting with a ceiling using `# ponytail: <ceiling>, <upgrade path>` (Python) or `// ponytail: …` (TS). Existing example: `getArticleById` in `frontend/app/lib/news.ts` filters a list client-side instead of adding a backend endpoint.
- Non-trivial logic (branch, loop, parser, money/security) leaves ONE runnable check: a small `test_*.py` (pytest is configured in `pyproject.toml`) or a TS type-level/`node` assert. No fixtures or per-function suites.
- **Never be lazy about:** input validation at trust boundaries, error handling that prevents data loss, security (secrets, auth), accessibility basics, anything the user explicitly asked for.
- Never skip the reading. Understand the full flow first, then pick the lowest rung.
- Output to the user: code first, then ≤3 lines on what was skipped and when to add it.

## 3. Architecture invariants (do not break)

1. **Two storage paths, deliberately.** RSS articles → SQLAlchemy over `DATABASE_URL` (Supabase Postgres connection). Twitter posts → Supabase REST client (`supabase-py`) into `twitter_posts`. Don't unify, migrate, or add a third path without asking. **No local Postgres**, ever.
2. **Layering (backend):** `api/` (HTTP only) → `db/`, `models/`, `schemas/` ; `scrapers/` fetch + normalize only; `tasks/` orchestrate scrapers + storage; `core/` config + constants. Routers never scrape; scrapers never touch the DB; tasks hold the persistence logic.
3. **Frontend talks only to the backend API**, and only through `frontend/app/lib/news.ts`. Components never call `fetch` on the API directly. No mock data — real backend data only.
4. **Server Components by default**; add `"use client"` only for state/effects/event handlers.
5. **Config lives in `core/config.py` (`Settings`) and `.env`.** Static lists (e.g. `TWITTER_ACCOUNTS`) live in `core/constants.py`. No `os.getenv` sprinkled around new code; no hard-coded URLs/keys.
6. **Secrets never in git.** New env var ⇒ add to `Settings` and the relevant `.env.example`. Supabase `service_role` key is server-side only; never expose it to the frontend.
7. **Ports are 8500+** (Redis 8500, backend 8501, frontend 8502). Any change updates `PORTS.md`, compose files, `.env.example`, and CORS (`cors_origins`).
8. **Scheduling lives in one place:** Celery beat schedule at the bottom of `backend/app/tasks/scrape.py`. RSS every 15 min, Twitter every `scrape_twitter_interval_hours` (6).
9. **Idempotent ingestion.** RSS dedupes on `Article.url`; Twitter upserts on `tweet_id`. New sources must do the same. Stale Twitter posts (older than the scrape interval) are dropped before storage (`TwitterScraper.tweet_to_record`).

## 4. Backend conventions (`backend/`, Python)

- **Structure:** one router module per resource in `app/api/`, registered in `app/main.py` with `prefix="/api/<name>"` and `tags`. Response shapes are Pydantic models in `app/schemas/`; ORM models in `app/models/`.
- **Scrapers** subclass `BaseScraper` (`app/scrapers/base.py`): implement `scrape()`, return dicts passed through `normalize_article()` so every source yields the same keys (`title, content, url, source, author, published_at, category, image_url`). Reuse `_parse_date`.
- **Celery tasks** are named explicitly (`@celery_app.task(name="scrape_…")`) and return a small status dict (`status`, counts, per-account detail). Return `"skipped"` with a message when config is missing; return `"error"`/`"auth_failed"` rather than raising for expected failures. Renaming a task needs a deprecated alias (see `scrape_twitter`).
- **Async at the edge, sync in workers.** FastAPI route handlers are `async def`; Celery tasks are sync and wrap async scrapers with `asyncio.run`.
- **DB sessions:** routes use `Depends(get_db)`; tasks open `SessionLocal()` and close it in `finally` with `rollback()` on error. Commit once per batch.
- **Errors:** raise `HTTPException` with accurate codes (503 not configured, 502 upstream/Supabase failure, 400 duplicate/bad input). Log with `logging.getLogger(__name__)` and `%s`-style args; no `print`.
- **Query params:** validate with `Query(..., ge=, le=)` bounds like existing routes (`limit` 1–100, `hours` 1–168). Never build SQL from strings; use the ORM or the Supabase client.
- **Style:** type hints on public functions, short docstring saying *why*, `list[str]`/`X | None` (3.12). New code shouldn't copy legacy habits: no bare `except:` (catch specific exceptions), use `datetime.now(timezone.utc)` instead of `utcnow()` in new code.
- **Subprocess (twitter-cli):** always pass `timeout`, capture output, never `shell=True`, never log cookie values.
- **Dependencies:** add via `pyproject.toml`. Check §2 rung 5 first.
- **Run:** `docker compose up` (see `QUICK_START.md`) or `cd backend && uv run uvicorn app.main:app --reload`. Tests: `cd backend && uv run pytest`.

## 5. Frontend conventions (`frontend/`, Next.js 16)

- **Read `node_modules/next/dist/docs/` first** (top of this file). Do not rely on memory of Next.js 13–15 APIs.
- **Layout:** pages in `app/` (`page.tsx`, `article/[id]/page.tsx`), shared components in `app/components/`, primitives in `app/components/ui/` (shadcn, config in `components.json`), data + helpers in `app/lib/`. Import via the `@/` alias.
- **Data access:** add API calls to `app/lib/news.ts` using the existing `fetchJson` (handles errors → `null`, `revalidate: 60`). Map API types to the UI type `FeedItem` there; components consume `FeedItem`, never raw API shapes.
- **Backend URL:** server-side uses `API_URL_SERVER` (falls back to `NEXT_PUBLIC_API_URL`, then `http://localhost:8501`). In Docker, `API_URL_SERVER` points at the backend service name.
- **Components:** function components, named exports for shared ones, default export only for route files. Props typed with `type` aliases. Handle the empty state (see `page.tsx`).
- **Styling:** Tailwind 4 utility classes, tokens from `globals.css` (`text-muted-foreground`, etc.), `cn()` from `app/lib/utils.ts` for conditional classes. Use existing `ui/` primitives (`Card`, `Badge`, `Button`, `Sheet`, `ScrollArea`, `Separator`) before building new ones; add new ones with the shadcn CLI, not by hand.
- **Icons:** `lucide-react`. **Package manager:** `pnpm` only.
- **External links** (tweets) use `target="_blank" rel="noopener noreferrer"`; internal links use `next/link`.
- **Accessibility:** semantic elements, visible focus, alt text, keyboard-reachable controls.
- **Checks before finishing:** `cd frontend && pnpm lint && pnpm build`.
- Design/animation work: the skills under `frontend/.agents/skills/` apply (e.g. `animate`, `apple-design`, `review-animations`); use them for UI polish tasks only.

## 6. Twitter scraper (`twitter-scraper/`)

- Standalone container; fetches via `twitter user-posts <handle> --json` (Agent-Reach / `twitter-cli`), **no browser/Chromium**.
- Auth is cookie-based (`TWITTER_AUTH_TOKEN`, `TWITTER_CT0`) from a throwaway account. Expired cookies surface as error code `not_authenticated` (`AUTH_ERROR_CODES`); handle that explicitly, don't retry in a loop.
- Be gentle on rate limits: keep the inter-account delay in the Celery task.
- To follow more accounts, edit `TWITTER_ACCOUNTS` in `backend/app/core/constants.py` — nothing else.

## 7. Reuse map — look here before writing new code

| Need | Use |
| --- | --- |
| Settings / env | `app.core.config.settings` |
| Static lists | `app.core.constants` |
| SQLAlchemy session | `app.db.session.get_db` / `SessionLocal` |
| Supabase client | `app.db.supabase_client.get_supabase_client`, `is_supabase_configured` |
| Date parsing | `BaseScraper._parse_date` |
| Normalized article dict | `BaseScraper.normalize_article` |
| Frontend API fetch | `fetchJson` in `frontend/app/lib/news.ts` |
| Relative time | `formatRelativeTime` in `frontend/app/lib/news.ts` |
| Class merging | `cn` in `frontend/app/lib/utils.ts` |

## 8. Git & workflow

- Small, focused commits; message says *why*. Don't commit unless asked. Don't force-push, and don't touch unrelated files.
- Don't edit lockfiles by hand; don't commit `.env` files.
- The Next.js agent block at the top of this file is auto-managed by `next dev`; keep it.
- Before declaring done: run the relevant check (backend `pytest`, frontend `pnpm lint && pnpm build`), and say plainly if you couldn't run it.

## 9. Definition of done

- [ ] Followed Ponytail ladder; no unrequested abstraction/dependency.
- [ ] Architecture invariants (§3) intact; layering respected.
- [ ] New env vars in `Settings` + `.env.example`; docs updated.
- [ ] Ingestion idempotent; errors handled at boundaries; no secrets logged.
- [ ] Lint/build/test run (or stated as not run).
