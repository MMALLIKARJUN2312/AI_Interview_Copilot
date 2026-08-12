# AI Interview Copilot

AI-powered interview preparation platform: upload a resume for a target role, get a
role-aligned ATS analysis, then take a role-aligned AI mock interview that produces
per-answer feedback, an overall assessment, and a personalized learning roadmap.

## Architecture

- **Frontend**: Next.js, TypeScript, Tailwind (`client/`) — auth, dashboard, resume
  upload/analysis, and the full mock-interview flow.
- **Backend**: FastAPI (`server/`)
- **Database**: PostgreSQL (+ pgvector extension, provisioned for future embeddings-based features)
- **AI**: Gemini (provider-abstracted; OpenAI/OpenRouter can be added behind the same interface)
- **Migrations**: Alembic
- **Auth**: JWT access tokens + rotating opaque refresh tokens
- **Storage**: pluggable resume storage backend (local disk by default, S3 opt-in)
- **Deployment**: Docker Compose (Postgres + API)

## Running locally with Docker

```bash
cp server/.env.example server/.env
# edit server/.env and set a real GEMINI_API_KEY and JWT_SECRET

docker compose up --build
```

This starts Postgres (with the pgvector extension available), runs `alembic upgrade head`,
and serves the API at `http://localhost:8000` (docs at `/docs`).

## Running the backend without Docker

```bash
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in DATABASE_URL, JWT_SECRET, GEMINI_API_KEY

alembic upgrade head
uvicorn main:app --reload
```

## Running the frontend

```bash
cd client
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

If `next dev` hits a Turbopack panic on your machine (seen on some Windows setups),
run `npm run dev -- --webpack` instead as a stable fallback.

## Running tests

```bash
cd server
pytest
```

Tests run against an in-memory SQLite database with rate limiting disabled and a faked
AI provider, so no live database, Gemini API key, or network access is required.

## Core flow

1. `POST /auth/register`, `POST /auth/login` — account creation and login. Login
   returns a short-lived JWT access token and a longer-lived opaque refresh token.
2. `POST /auth/refresh` — exchange a refresh token for a new access/refresh pair
   (rotates the old refresh token, so it can't be reused). `POST /auth/logout` revokes one.
3. `POST /resume/analyze` — upload a PDF resume with a `target_role` (and optional
   `job_description`); returns a role-aware ATS score, strengths, weaknesses, and
   suggestions. The resume and analysis are persisted; the file itself goes through
   the configured storage backend (local disk or S3).
4. `POST /interview/start` — generates a set of interview questions grounded in that
   specific resume and role.
5. `POST /interview/{id}/answer` — submit an answer to the current question; returns
   an AI-scored evaluation and the next question.
6. `POST /interview/{id}/complete` — once all questions are answered, produces an
   overall performance summary and a personalized learning roadmap.
7. `GET /interview/{id}`, `GET /interview/sessions`, `GET /resume/` — review history.
8. `GET /health` — liveness probe for orchestration/load balancers.

Auth, resume-analysis, and interview-generation/answer/complete endpoints are rate
limited per IP (see `app/core/rate_limit.py` for the exact limits); disable via
`RATE_LIMIT_ENABLED=false` for local testing.

## Status

Full loop works end-to-end: resume upload → role-aligned mock interview → feedback →
roadmap, with a working frontend, refresh-token auth, rate limiting, pluggable resume
storage, and a pytest suite. Still open: CI, pgvector-grounded question generation
(currently pure zero-shot), and a persistent Redis-backed rate-limit store (current
limiter is in-memory, fine for a single instance).
