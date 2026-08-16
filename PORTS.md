# Port Configuration

All host ports are consecutive, starting at **8500**, to avoid clashing
with common local dev ports (3000, 5432, 6379, 8000, etc.) and tools like
OrbStack. There is no local Postgres port - the database is Supabase.

## Services

| Service         | Host Port | Container Port | URL                          |
| ---------------- | --------- | --------------- | ----------------------------- |
| **Redis**         | 8500      | 6379             | `redis://localhost:8500/0`   |
| **Backend API**   | 8501      | 8000             | http://localhost:8501         |
| **Backend Docs**  | 8501      | 8000             | http://localhost:8501/docs    |
| **Frontend**      | 8502      | 3000             | http://localhost:8502         |

The Twitter scraper (`twitter-scraper/`) doesn't expose any host port - it
only talks to the backend over the internal Docker network.

**Database:** Supabase (Postgres), not a local container. Both RSS
articles (via `DATABASE_URL`, a direct Postgres connection) and scraped
Twitter posts (via `SUPABASE_URL`/`SUPABASE_KEY`, the Supabase REST API)
live there. See `backend/.env.example`.

## Twitter Scraper

Built on [Agent-Reach](https://github.com/Panniantong/Agent-Reach) /
`twitter-cli` - no browser, no Chromium. See `twitter-scraper/README.md`.

## Changing the Ports

Ports are set in each service's own compose file. Edit the `ports:` mapping
and any `localhost:<port>` references in the same file:

- `docker-compose.redis.yml`: `8500:6379`
- `docker-compose.backend.yml`: `8501:8000`, plus `CORS_ORIGINS` (must match
  the frontend's host port)
- `docker-compose.frontend.yml`: `8502:3000`, plus `NEXT_PUBLIC_API_URL`
  (must match the backend's host port)

Also update the matching defaults in `backend/.env.example`,
`backend/app/core/config.py`, and `frontend/.env.example` if you want local
(non-Docker) dev to use the same ports.

Then rebuild: `docker compose up --build`

See [`CONTAINERS.md`](./CONTAINERS.md) for the exact command to start each
container individually.
