# Port Configuration

All host ports are consecutive, starting at **8500**, to avoid clashing
with common local dev ports (3000, 5432, 6379, 8000, etc.) and tools like
OrbStack. Persistence uses the local `data/news.json` file.

## Services

| Service         | Host Port | Container Port | URL                          |
| ---------------- | --------- | --------------- | ----------------------------- |
| **Redis**         | 8500      | 6379             | `redis://localhost:8500/0`   |
| **Backend API**   | 8501      | 8000             | http://localhost:8501         |
| **Backend Docs**  | 8501      | 8000             | http://localhost:8501/docs    |
| **Frontend**      | 8502      | 3000             | http://localhost:8502         |

The Twitter scraper (`twitter-scraper/`) doesn't expose any host port - it
only talks to the backend over the internal Docker network.

**Data:** RSS articles, sources, X posts, and X replies are stored in
`data/news.json` and exposed through the backend API.

## Twitter Scraper

Built on [Agent-Reach](https://github.com/Panniantong/Agent-Reach) /
`twitter-cli` - no browser, no Chromium. See `twitter-scraper/README.md`.

## Changing the Ports

Ports are set in each service's own compose file. Edit the `ports:` mapping
and any `localhost:<port>` references in the same file:

- `docker-compose.redis.yml`: `8500:6379`
- `docker-compose.backend.yml`: `8501:8000`, plus `CORS_ORIGINS` (must match
  the frontend's host port)
- `docker-compose.frontend.yml`: `8502:3000`. The frontend uses the backend
  API on port 8501.

Also update the matching defaults in `backend/.env.example` and
`backend/app/core/config.py` if you want local development to use the same ports.

Then rebuild: `docker compose up --build`

See [`CONTAINERS.md`](./CONTAINERS.md) for the exact command to start each
container individually.
