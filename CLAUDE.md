@AGENTS.md

# Claude Code specifics

`AGENTS.md` (imported above) is the full architecture guide and coding standard. These are the Claude-only additions.

## Compulsory before writing any code

1. **Invoke the `ponytail:ponytail` skill (Skill tool) at the start of every coding task** — writing, editing, refactoring, fixing, reviewing, or picking a dependency. Skipping it is a violation of this file. Use `ponytail:ponytail-review` when reviewing a diff and `ponytail:ponytail-audit` for a whole-repo bloat pass.
2. **Re-read the matching section of `AGENTS.md`** (backend §4, frontend §5, scraper §6) and the architecture invariants (§3) before touching code.
3. **For anything under `frontend/`, read the relevant doc in `frontend/node_modules/next/dist/docs/` first.** Next.js here is 16.x; don't trust memory.
4. **Grep for an existing helper before writing one** (see the reuse map in `AGENTS.md` §7).

## Behavior

- Maintain the architecture. If a request would break an invariant in `AGENTS.md` §3 (storage paths, layering, frontend→API only via `app/lib/news.ts`, ports, scheduling location), say so and ask before proceeding.
- Prefer the smallest correct diff. Ship the lazy version and question it in one line ("Did X; Y covers it. Need full X? Say so.") rather than stalling.
- Fix bugs at the root: grep all callers first, fix in the shared function.
- Use dedicated tools (Read/Edit/Grep/Glob) over shell equivalents.
- Don't commit, push, or touch git history unless asked. Never print or commit secrets (`.env`, Supabase keys, Twitter cookies).
- Keep `AGENTS.md`/`CLAUDE.md` current: if you change architecture, ports, env vars, or conventions, update them in the same change.
- Verify before finishing: backend `cd backend && uv run pytest`; frontend `cd frontend && pnpm lint && pnpm build`. If you can't run a check, say so.

## Quick commands

| Task | Command |
| --- | --- |
| Run everything | `docker compose up` (see `QUICK_START.md`) |
| Backend dev | `cd backend && uv run uvicorn app.main:app --reload` |
| Frontend dev | `cd frontend && pnpm dev` |
| Backend tests | `cd backend && uv run pytest` |
| Frontend checks | `cd frontend && pnpm lint && pnpm build` |
