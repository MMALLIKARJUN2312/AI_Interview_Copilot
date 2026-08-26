# AI Interview Copilot

[![CI](https://github.com/MMALLIKARJUN2312/AI_Interview_Copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/MMALLIKARJUN2312/AI_Interview_Copilot/actions/workflows/ci.yml)

AI Interview Copilot is an AI-powered interview preparation platform. Users upload a PDF resume for a target role, receive a role-aligned ATS analysis, and complete AI-generated mock interviews across:

- DSA coding
- Machine coding
- Technical questions
- System-design questions
- Behavioral questions

Each submitted answer receives feedback and a score. Completed interviews produce an overall assessment and a personalized learning roadmap.

## Features

- User registration and login
- Rotating refresh-token authentication
- PDF resume upload and text extraction
- Role-specific ATS analysis
- Job-description-aware recommendations
- Configurable multi-round mock interviews
- DSA and machine-coding rounds
- Real code execution through a self-hosted Piston service
- Hidden and visible coding test cases
- AI-generated answer evaluation
- Interview summaries and learning roadmaps
- Resume and interview history
- AI-provider retry and failover
- Local and S3-compatible resume storage
- Request rate limiting
- PostgreSQL and Alembic migrations
- Automated backend, migration, frontend, and Docker CI checks
- Production Docker images

## Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL with pgvector |
| Migrations | Alembic |
| Authentication | JWT access tokens and rotating opaque refresh tokens |
| AI | Gemini, Groq and OpenRouter provider chain |
| Code execution | Self-hosted Piston-compatible API |
| Storage | Local filesystem or S3-compatible object storage |
| Development | Docker Compose |
| CI | GitHub Actions |

```text
Browser
   |
   v
Next.js frontend
   |
   v
FastAPI backend
   |
   +---- PostgreSQL
   |
   +---- AI provider chain
   |       Gemini -> Groq -> OpenRouter
   |
   +---- Piston code-execution service
   |
   +---- Local or S3 resume storage
```

## Repository structure

```text
AI_Interview_Copilot/
├── .github/
│   └── workflows/
│       └── ci.yml
├── client/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── DEPLOYMENT.md
│   └── system-design.md
├── server/
│   ├── alembic/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Prerequisites

Install the following:

- Git
- Docker Desktop or Docker Engine
- Docker Compose v2
- Node.js 20
- npm
- Python 3.11 for native backend development

At least one AI-provider API key is required:

- Gemini: <https://aistudio.google.com/apikey>
- Groq: <https://console.groq.com>
- OpenRouter: <https://openrouter.ai>

## Clone the repository

```bash
git clone https://github.com/MMALLIKARJUN2312/AI_Interview_Copilot.git
cd AI_Interview_Copilot
```

## Configure the backend

### Linux or macOS

```bash
cp server/.env.example server/.env
```

### Windows PowerShell

```powershell
Copy-Item server\.env.example server\.env
```

Edit `server/.env` and configure at least:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_interview_copilot

JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

AI_PROVIDER_CHAIN=gemini,groq
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key

CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=true

STORAGE_BACKEND=local
LOCAL_STORAGE_DIR=uploads/resumes

CODE_EXECUTION_API_URL=http://localhost:2000/api/v2
CODE_EXECUTION_TIMEOUT_SECONDS=15
```

Only add a provider to `AI_PROVIDER_CHAIN` when its corresponding API key is configured.

Never commit `server/.env`.

## Start self-hosted Piston

Coding questions require a Piston-compatible code-execution service. The application defaults to:

```text
http://localhost:2000/api/v2
```

The public Piston API is not a dependable fallback for this project. Run a self-hosted instance locally.

Piston requires Linux containers and privileged container support.

### Create and start the container

```bash
docker volume create piston_data

docker run \
  --privileged \
  --volume piston_data:/piston \
  --detach \
  --publish 2000:2000 \
  --name piston_api \
  ghcr.io/engineer-man/piston
```

Windows PowerShell:

```powershell
docker volume create piston_data

docker run --privileged `
  --volume piston_data:/piston `
  --detach `
  --publish 2000:2000 `
  --name piston_api `
  ghcr.io/engineer-man/piston
```

Check the service:

```bash
curl http://localhost:2000/api/v2/runtimes
```

PowerShell:

```powershell
Invoke-RestMethod http://localhost:2000/api/v2/runtimes
```

A new Piston installation contains no language runtimes. Install the versions expected by `server/app/core/constants.py`.

PowerShell:

```powershell
$runtimes = @(
    @{ language = "python"; version = "3.12.0" },
    @{ language = "javascript"; version = "20.11.1" },
    @{ language = "java"; version = "15.0.2" },
    @{ language = "c++"; version = "10.2.0" }
)

foreach ($runtime in $runtimes) {
    Invoke-RestMethod `
        -Method Post `
        -Uri "http://localhost:2000/api/v2/packages" `
        -ContentType "application/json" `
        -Body ($runtime | ConvertTo-Json)
}
```

Linux or macOS:

```bash
curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"python","version":"3.12.0"}'

curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"javascript","version":"20.11.1"}'

curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"java","version":"15.0.2"}'

curl -X POST http://localhost:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"c++","version":"10.2.0"}'
```

Verify the installed runtimes:

```bash
curl http://localhost:2000/api/v2/runtimes
```

Useful lifecycle commands:

```bash
docker logs piston_api
docker stop piston_api
docker start piston_api
docker rm -f piston_api
```

Do not expose an unauthenticated Piston instance directly to the public internet.

## Run PostgreSQL and the backend with Docker

When the FastAPI backend runs inside Docker Desktop and Piston runs as a separate host container, update `server/.env`:

```env
CODE_EXECUTION_API_URL=http://host.docker.internal:2000/api/v2
```

Start PostgreSQL and the API:

```bash
docker compose up --build -d
```

Inspect the services:

```bash
docker compose ps
docker compose logs -f api
```

The Compose API command applies migrations before starting FastAPI.

Available endpoints:

- API: <http://localhost:8000>
- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- PostgreSQL: `localhost:5432`
- Piston: <http://localhost:2000/api/v2>

Verify the backend:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run the frontend

Open another terminal:

```bash
cd client
npm ci
```

Create `client/.env.local`.

Linux or macOS:

```bash
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\n' > .env.local
```

Windows PowerShell:

```powershell
Set-Content .env.local "NEXT_PUBLIC_API_URL=http://localhost:8000"
```

Start Next.js:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

If Turbopack fails on Windows, use Webpack:

```bash
npm run dev -- --webpack
```

## Run the backend natively

Start only PostgreSQL through Docker:

```bash
docker compose up -d db
```

Keep Piston running on port `2000` and use:

```env
CODE_EXECUTION_API_URL=http://localhost:2000/api/v2
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_interview_copilot
```

### Linux or macOS

```bash
cd server
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

### Windows PowerShell

```powershell
cd server
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

If PowerShell blocks virtual-environment activation, run the environment’s Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

## Run tests

Backend tests use in-memory SQLite, fake AI responses, fake code execution and disabled rate limiting. They do not require PostgreSQL, Piston, network access or real provider keys.

```bash
cd server
pytest -q
```

If Windows reports that access to `AppData\Local\Temp\pytest-of-<username>` is denied, give pytest a project-local temporary directory:

```powershell
pytest -q --basetemp=.pytest-tmp
```

Remove that temporary directory afterward:

```powershell
Remove-Item -Recurse -Force .pytest-tmp
```

The current backend suite contains 61 tests.

Run the same frontend checks used by CI:

```bash
cd client
npm ci
npx tsc --noEmit
npm run lint
npm run build
```

## AI provider configuration

`AI_PROVIDER_CHAIN` is an ordered, comma-separated provider list:

```env
AI_PROVIDER_CHAIN=gemini,groq,openrouter
```

Each provider retries transient failures before the application moves to the next provider.

| Provider | API-key variable | Default model |
|---|---|---|
| Gemini | `GEMINI_API_KEY` | `gemini-3.5-flash-lite` |
| Groq | `GROQ_API_KEY` | `openai/gpt-oss-120b` |
| OpenRouter | `OPENROUTER_API_KEY` | `meta-llama/llama-3.3-70b-instruct:free` |

Model availability changes over time. Override the corresponding model environment variable when a provider retires or replaces a model.

## Application flow

1. A user creates an account.
2. Successful registration redirects the user to the login screen.
3. Login returns an access token and a rotating refresh token.
4. The user uploads a PDF resume and selects a target role.
5. The backend extracts the resume text and requests an AI analysis.
6. The user creates a mock interview with one or more round types.
7. The backend generates role-aligned questions.
8. General answers are evaluated by the configured AI provider chain.
9. Coding answers are executed through Piston and reviewed by AI.
10. DSA scores combine test-case results with AI feedback.
11. An interview can be completed only after every question is answered.
12. Completion generates overall feedback and a learning roadmap.

## Important API routes

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Authenticate |
| `POST` | `/auth/refresh` | Rotate refresh token |
| `POST` | `/auth/logout` | Revoke refresh token |
| `GET` | `/auth/me` | Get the current user |
| `POST` | `/resume/analyze` | Upload and analyze a resume |
| `GET` | `/resume/` | List resumes |
| `POST` | `/interview/start` | Generate an interview |
| `POST` | `/interview/{id}/run-code` | Run code without submitting |
| `POST` | `/interview/{id}/answer` | Submit and evaluate an answer |
| `POST` | `/interview/{id}/complete` | Complete a fully answered interview |
| `GET` | `/interview/sessions` | List interview sessions |
| `GET` | `/interview/{id}` | Get interview details |
| `GET` | `/health` | Liveness check |

## Continuous integration

`.github/workflows/ci.yml` runs on pushes and pull requests targeting `main`.

It verifies:

- Backend tests on Python 3.11
- Alembic migrations against fresh PostgreSQL with pgvector
- Frontend TypeScript compilation
- Frontend ESLint checks
- Next.js production build
- FastAPI Docker image build
- Next.js Docker image build

CI validates the project but does not deploy it automatically.

## Production deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:

- Vercel frontend deployment
- Render backend deployment
- PostgreSQL configuration
- S3 resume storage
- Self-hosted Piston requirements
- Docker Compose deployment
- Production verification
- Free-tier limitations

## Current limitations

Before treating the application as a commercial SaaS, address:

- Browser refresh tokens are currently stored in local storage.
- AI processing occurs inside HTTP requests instead of background jobs.
- Rate limiting uses process memory instead of a shared Redis store.
- Local resume storage supports only a single persistent API instance.
- Piston requires separate privileged Linux infrastructure.
- Historical migrations require a data-preservation audit.
- Python dependencies are not fully locked.
- Billing, subscriptions and account-level quotas are not implemented.
- Email verification and password recovery are not implemented.
- CI does not currently perform production deployment.

## License

No license has been added yet. Add an appropriate license before encouraging external contributions or reuse.
