# Twitter Scraper - Current Status

## ✅ Rebuilt on Agent-Reach (2026-08-16)

The scraper installs and uses
[Agent-Reach](https://github.com/Panniantong/Agent-Reach) directly rather
than hardcoding a Twitter backend. Agent-Reach's own installer
(`agent-reach install --channels=twitter`) provisions `twitter-cli` -
currently their selected Twitter backend - inside the image; the scraper
shells out to whatever `twitter` command that installer set up.

An earlier iteration used `twitter-cli` directly without going through
Agent-Reach; this was replaced per explicit request to integrate the actual
Agent-Reach project. Before that, the original scraper used
Playwright/Chromium and failed to build on ARM64 (see [`../STATUS.md`](../STATUS.md)
for that history) - there's no browser in this image at all, so that class
of problem doesn't apply anymore.

```bash
docker compose -f docker-compose.twitter-scraper.yml up -d --build
```

## Summary

- **Base image**: `python:3.12-slim` + Agent-Reach installed via `pipx`
  from its GitHub source (not PyPI - see README for why). No Chromium.
- **Backend selection**: delegated to Agent-Reach. `agent-reach doctor`
  reports the active backend and credential status; logged on every
  scraper startup for visibility.
- **Auth is required**: X does not allow meaningful anonymous access.
  Set `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` in a repo-root `.env` file
  (see `twitter-scraper/README.md` for how to export these with
  Cookie-Editor - Agent-Reach's own docs recommend a throwaway account).
- **Input**: a comma-separated list of profile URLs (or bare handles) via
  `TWITTER_PROFILE_URLS`.

## Verified (2026-08-16)

- `docker compose -f docker-compose.twitter-scraper.yml build twitter-scraper` succeeds
- `agent-reach --version` and `twitter --version` both work inside the built image
- `agent-reach doctor --json` correctly reports the twitter channel
  (`active_backend`, credential warnings) from inside the container
- Full stack (`up -d`) starts cleanly; without cookies configured, the
  scraper logs Agent-Reach's own doctor diagnosis and then a clean
  per-profile 0-posts warning instead of crashing
