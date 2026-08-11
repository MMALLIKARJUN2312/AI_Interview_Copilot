# AI Interview Copilot

AI-powered interview preparation platform: upload a resume for a target role, get a
role-aligned ATS analysis, then take a role-aligned AI mock interview that produces
per-answer feedback, an overall assessment, and a personalized learning roadmap.

## Architecture

- **Frontend**: Next.js, TypeScript, Tailwind (`client/`)
- **Backend**: FastAPI (`server/`)
- **Database**: PostgreSQL (+ pgvector extension, provisioned for future embeddings-based features)
- **AI**: Gemini (provider-abstracted; OpenAI/OpenRouter can be added behind the same interface)
- **Migrations**: Alembic
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

## Running tests

```bash
cd server
pytest
```

Tests run against an in-memory SQLite database and a faked AI provider, so no live
database or Gemini API key is required.

## Core flow

1. `POST /auth/register`, `POST /auth/login` — account + JWT auth.
2. `POST /resume/analyze` — upload a PDF resume with a `target_role` (and optional
   `job_description`); returns a role-aware ATS score, strengths, weaknesses, and
   suggestions. The resume and analysis are persisted.
3. `POST /interview/start` — generates a set of interview questions grounded in that
   specific resume and role.
4. `POST /interview/{id}/answer` — submit an answer to the current question; returns
   an AI-scored evaluation and the next question.
5. `POST /interview/{id}/complete` — once all questions are answered, produces an
   overall performance summary and a personalized learning roadmap.
6. `GET /interview/{id}`, `GET /interview/sessions`, `GET /resume/` — review history.

## Status

Backend covers the full resume → role-aligned mock interview → feedback → roadmap
loop. Still open: frontend UI (currently an unbuilt Next.js scaffold), refresh-token
rotation, rate limiting, object storage for uploaded resumes, and CI.
