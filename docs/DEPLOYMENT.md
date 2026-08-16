# Production deployment

This covers deploying AI Interview Copilot with `docker-compose.prod.yml`: Postgres
(+pgvector), the FastAPI backend, and the Next.js frontend, each in its own
container, built from production Dockerfiles.

This is one deployment path among several reasonable ones (a single Docker host is
enough for moderate traffic). If you're deploying to a platform that builds
containers for you (Fly.io, Render, Railway, ECS, etc.), skip the Compose file and
point the platform at `server/Dockerfile` and `client/Dockerfile` directly — the
[Building the images manually](#building-the-images-manually) and
[Configuration reference](#configuration-reference) sections below still apply.

## Prerequisites

- Docker and Docker Compose v2 (`docker compose version`)
- A Gemini API key ([aistudio.google.com/apikey](https://aistudio.google.com/apikey))
- A domain (or IP) the two services will be reachable at, so you can fill in
  `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` correctly before building

## 1. Configure environment

**Backend** — copy and fill in `server/.env`:

```bash
cp server/.env.example server/.env
```

At minimum, set for production:

- `JWT_SECRET` — a long random value (`openssl rand -hex 32`), different from any
  value used in development
- `GEMINI_API_KEY` — your real key
- `CORS_ORIGINS` — the exact origin(s) the frontend is served from, e.g.
  `https://app.example.com` (no trailing slash, comma-separate multiple origins)
- `RATE_LIMIT_ENABLED=true`
- `STORAGE_BACKEND` — see [Resume storage](#resume-storage) below

**Root `.env`** (read by `docker-compose.prod.yml` itself, not by the app) — create
one next to `docker-compose.prod.yml`:

```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<a strong random password>
POSTGRES_DB=ai_interview_copilot
NEXT_PUBLIC_API_URL=https://api.example.com
```

`NEXT_PUBLIC_API_URL` is baked into the frontend's JavaScript bundle at build
time (Next.js inlines `NEXT_PUBLIC_*` vars at build, not at container start) — if
it changes, the `web` image must be rebuilt, not just restarted.

Neither `.env` file should be committed; both are already covered by the repo's
`.gitignore`.

## 2. Build and start

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

This builds the two production images, starts Postgres, waits for it to report
healthy, runs `alembic upgrade head` against it, then starts the API (2 uvicorn
workers) and the frontend. Postgres itself is not published to the host — only
reachable from the `api` container on the internal Compose network.

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health   # {"status": "ok"}
curl -I http://localhost:3000
```

## 3. Put a reverse proxy in front

Neither container terminates TLS. In production, put a reverse proxy in front of
both — e.g. a minimal Caddy config:

```caddyfile
app.example.com {
    reverse_proxy localhost:3000
}

api.example.com {
    reverse_proxy localhost:8000
}
```

Caddy handles Let's Encrypt certificates automatically here; Nginx + certbot, or
your cloud provider's load balancer, work the same way — just make sure
`CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` match whatever public hostnames you land
on before building.

## Building the images manually

If you're not using the Compose file:

```bash
docker build -t ai-interview-copilot-api ./server

docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
  -t ai-interview-copilot-web ./client
```

The API container expects `server/.env` values as environment variables (via
`--env-file server/.env` or your platform's secrets mechanism) and needs
`DATABASE_URL` pointed at a reachable Postgres instance. Run
`alembic upgrade head` once before (or as part of) the container's start command —
the image does not run migrations automatically on its own.

## Configuration reference

| Variable | Where | Notes |
|---|---|---|
| `DATABASE_URL` | server | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET` | server | rotate this and all issued tokens become invalid |
| `GEMINI_API_KEY` | server | |
| `CORS_ORIGINS` | server | must exactly match the frontend's origin(s) |
| `RATE_LIMIT_ENABLED` | server | keep `true` in production |
| `STORAGE_BACKEND` | server | `local` or `s3`, see below |
| `CODE_EXECUTION_API_URL` | server | Piston-compatible code execution backend, see below |
| `NEXT_PUBLIC_API_URL` | client (build-time) | public URL the browser calls |

## Code execution (DSA / machine-coding rounds)

Coding-round questions execute candidate-submitted code via a
[Piston](https://github.com/engineer-man/piston)-compatible API, configured by
`CODE_EXECUTION_API_URL` (defaults to the free public instance,
`https://emkc.org/api/v2/piston`). The public instance is rate-limited and not
meant for production load — self-host Piston (a single Docker container) and
point `CODE_EXECUTION_API_URL` at it before taking real traffic. All code
execution sandboxing happens entirely inside Piston; this app never executes
candidate code itself.

## Resume storage

`STORAGE_BACKEND=local` (the default) writes uploaded resumes to a volume inside
the `api` container. This only works correctly with a **single** API instance —
if you scale `api` beyond one replica, each replica sees a different disk and
resume lookups will fail on whichever replica didn't handle the upload.

For anything beyond a single instance, set `STORAGE_BACKEND=s3` and fill in
`S3_BUCKET_NAME` / `AWS_REGION` in `server/.env`. AWS credentials are picked up
from the standard boto3 credential chain (environment variables, an attached IAM
role, etc.) — never put access keys directly in `.env`.

## Database migrations on deploy

Every deploy that changes `server/alembic/versions/` needs `alembic upgrade head`
run against production before (or as) the new API version starts — the
`docker-compose.prod.yml` `api` service already does this in its start command.
If you deploy the API without Compose, run it as a separate step in your deploy
pipeline, before traffic is routed to the new containers.

## Logs and health

- `GET /health` on the API returns `{"status": "ok"}` — use it as your load
  balancer / orchestrator's health check.
- Both Dockerfiles declare a container-level `HEALTHCHECK`, visible in
  `docker compose ps` / `docker inspect`.
- The API logs one line per request (method, path, status, duration) plus full
  tracebacks for unhandled exceptions, via Python's standard `logging` module
  (stderr by default) — collect it with whatever your platform already uses for
  container logs (no separate log shipper is wired up).

## CI

`.github/workflows/ci.yml` runs backend tests, a migration check against a real
Postgres, and frontend lint/typecheck/build on every push and PR — it does not
deploy anywhere. Wiring an actual deploy (e.g. build+push images, then update a
running service) is a deliberate next step, not something this repo does today.
