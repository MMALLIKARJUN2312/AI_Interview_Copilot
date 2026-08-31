# Deployment guide

This document describes two deployment paths for AI Interview Copilot:

1. Vercel for the Next.js frontend and Render for the FastAPI backend.
2. A single Linux Docker host using `docker-compose.prod.yml`.

The first option is convenient for a personal demonstration or beta. The second provides more control and makes self-hosting Piston easier.

## Production architecture

```text
Users
  |
  v
Vercel
Next.js frontend
  |
  v
Render
FastAPI backend
  |
  +---- Managed PostgreSQL
  |
  +---- S3-compatible object storage
  |
  +---- Gemini / Groq / OpenRouter
  |
  +---- Privately hosted Piston service
```

## Important limitations

Read these before deployment:

- Vercel Hobby is intended for personal, non-commercial projects.
- Render free web services sleep after inactivity and have cold starts.
- Render free PostgreSQL databases expire after 30 days.
- Render’s service filesystem is ephemeral.
- `STORAGE_BACKEND=local` is not suitable for an ephemeral web service.
- Piston requires privileged Linux container capabilities.
- Do not expose Piston directly to the public internet.
- The current GitHub Actions workflow performs CI but not automatic deployment.
- The current application performs AI work synchronously during HTTP requests.
- Production data should not rely on free services without backups.

## Prerequisites

- A GitHub repository containing the application
- A Vercel account
- A Render account
- A managed PostgreSQL database
- An S3-compatible private bucket
- At least one supported AI-provider API key
- A Linux environment capable of running Piston
- Optional custom domains for the frontend and backend

## Required production secrets

The backend requires:

```env
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

AI_PROVIDER_CHAIN=gemini,groq
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

CORS_ORIGINS=
RATE_LIMIT_ENABLED=true

STORAGE_BACKEND=s3
S3_BUCKET_NAME=
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

CODE_EXECUTION_API_URL=
CODE_EXECUTION_TIMEOUT_SECONDS=15
```

Generate `JWT_SECRET` with a cryptographically secure generator.

Linux:

```bash
openssl rand -hex 32
```

PowerShell:

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToHexString($bytes).ToLower()
```

Never commit production secrets.

## Deploy PostgreSQL on Render

Create a Render PostgreSQL database in the same region as the backend.

Copy its internal connection URL and configure it as:

```env
DATABASE_URL=<render-internal-postgresql-url>
```

Production recommendations:

- Use a paid database if data must survive longer than 30 days.
- Enable available backups or point-in-time recovery.
- Keep PostgreSQL inaccessible from the public internet when possible.
- Store and test logical backups separately.
- Audit historical migrations before upgrading a database containing important data.

The database must support the `vector` extension used by pgvector.

## Deploy the FastAPI backend on Render

Create a new Render Web Service connected to the GitHub repository.

Recommended settings:

| Setting | Value |
|---|---|
| Runtime | Docker |
| Branch | `main` |
| Dockerfile path | `server/Dockerfile` |
| Health-check path | `/health` |
| Auto-deploy | After CI checks pass |
| Region | Same region as PostgreSQL |

The Docker build context must be the `server` directory. Depending on the Render interface, configure either:

```text
Root directory: server
Dockerfile path: ./Dockerfile
```

or:

```text
Dockerfile path: server/Dockerfile
Docker context: server
```

### Render start command

The current Docker image starts Uvicorn on port `8000`. Render can discover an exposed port, but explicitly using the platform-provided port is safer.

Set the Docker command to:

```sh
/bin/sh -c 'alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}'
```

For a personal beta using one API instance, running migrations immediately before startup is acceptable.

Before scaling to multiple API instances, move:

```bash
alembic upgrade head
```

into Render’s pre-deploy command so only one migration process runs per release.

### Backend environment variables

Configure the variables from the production secret reference in Render’s environment settings.

For example:

```env
DATABASE_URL=<render-internal-database-url>
JWT_SECRET=<generated-secret>

AI_PROVIDER_CHAIN=gemini,groq
GEMINI_API_KEY=<secret>
GROQ_API_KEY=<secret>

CORS_ORIGINS=https://your-vercel-domain.vercel.app
RATE_LIMIT_ENABLED=true

STORAGE_BACKEND=s3
S3_BUCKET_NAME=<private-bucket-name>
AWS_REGION=<bucket-region>
AWS_ACCESS_KEY_ID=<secret>
AWS_SECRET_ACCESS_KEY=<secret>

CODE_EXECUTION_API_URL=http://private-piston-host:2000/api/v2
CODE_EXECUTION_TIMEOUT_SECONDS=15
```

The CORS origin must:

- include `https://`;
- exactly match the frontend origin;
- not include a trailing slash;
- use comma separation if multiple origins are required.

Example:

```env
CORS_ORIGINS=https://app.example.com,https://preview.example.com
```

Do not configure unrestricted CORS for an authenticated production API.

## Deploy the frontend on Vercel

Import the GitHub repository into Vercel.

Configure:

| Setting | Value |
|---|---|
| Framework | Next.js |
| Root directory | `client` |
| Install command | `npm ci` |
| Build command | `npm run build` |
| Production branch | `main` |

Add this Vercel production environment variable:

```env
NEXT_PUBLIC_API_URL=https://your-api.onrender.com
```

`NEXT_PUBLIC_API_URL` is embedded into the browser bundle during the Next.js build. Redeploy the frontend whenever it changes.

After Vercel assigns the final frontend URL, update Render:

```env
CORS_ORIGINS=https://your-final-vercel-domain.vercel.app
```

Redeploy the backend after changing CORS.

For a custom domain:

```env
NEXT_PUBLIC_API_URL=https://api.example.com
CORS_ORIGINS=https://app.example.com
```

Use a separate backend and database for preview deployments if previews should not access production data.

## Configure production resume storage

Do not use local storage on Render.

Render’s filesystem is ephemeral, which means uploaded files can disappear after:

- deployments;
- restarts;
- free-service sleep cycles;
- service replacement.

Configure:

```env
STORAGE_BACKEND=s3
S3_BUCKET_NAME=<bucket-name>
AWS_REGION=<region>
```

Provide credentials through Render’s secret environment variables or an attached identity mechanism.

The bucket should:

- be private;
- block public access;
- encrypt objects at rest;
- grant the backend only the required permissions;
- define file-retention rules;
- support deletion when a user deletes their data;
- log administrative access where available.

Never place access keys in the repository.

## Deploy Piston

The project expects a self-hosted Piston-compatible API.

The public Piston API is no longer generally available as a free anonymous service. Do not design production deployment around it.

Piston requires:

- Linux
- Docker
- privileged container support
- cgroup support
- persistent runtime-package storage
- isolation from the public internet

A conventional restricted application platform might not provide the privileged container capabilities required by Piston. Host it on a dedicated Linux VM or another environment where privileged Docker containers and cgroups are supported.

### Start Piston on a Linux host

```bash
docker volume create piston_data

docker run \
  --privileged \
  --volume piston_data:/piston \
  --detach \
  --restart unless-stopped \
  --publish 127.0.0.1:2000:2000 \
  --name piston_api \
  ghcr.io/engineer-man/piston
```

Binding to `127.0.0.1` prevents direct external access. Place an authenticated internal proxy, VPN or private-network service in front when the FastAPI backend runs on another host.

### Install required runtimes

```bash
curl -X POST http://127.0.0.1:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"python","version":"3.12.0"}'

curl -X POST http://127.0.0.1:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"javascript","version":"20.11.1"}'

curl -X POST http://127.0.0.1:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"java","version":"15.0.2"}'

curl -X POST http://127.0.0.1:2000/api/v2/packages \
  -H "Content-Type: application/json" \
  -d '{"language":"c++","version":"10.2.0"}'
```

Verify:

```bash
curl http://127.0.0.1:2000/api/v2/runtimes
docker logs piston_api
```

Configure the backend with a private endpoint reachable only through a private network, VPN, firewall allowlist or internal service network:

```env
CODE_EXECUTION_API_URL=https://private-code-runner.example.com/api/v2
```

Production Piston controls should include:

- no direct public access;
- outbound networking disabled for submitted programs;
- strict execution time limits;
- strict memory and process limits;
- private-network or firewall-based access control;
- request authentication after backend support for an authorization header is implemented;
- per-user execution quotas;
- API rate limits;
- request and error monitoring;
- limited output size;
- regular image and runtime updates.

Do not run Piston inside the FastAPI container.

## Validate the Vercel and Render deployment

Check the backend:

```bash
curl https://your-api.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

Check the frontend:

```bash
curl -I https://your-frontend.vercel.app
```

Check CORS from a browser by:

1. Opening the deployed frontend.
2. Creating an account.
3. Confirming signup redirects to login.
4. Logging in.
5. Uploading a small PDF.
6. Creating a general interview.
7. Answering every generated question.
8. Completing the interview.
9. Confirming feedback and roadmap persistence.
10. Starting a coding interview and verifying Piston execution.

Also verify:

- registration does not automatically authenticate the user;
- partial interviews cannot be completed;
- refresh-token rotation works;
- resumes remain available after backend redeployment;
- database records remain available after backend redeployment;
- no hidden test cases appear in API responses;
- provider failover works when the first provider is unavailable.

## Deploy with Docker Compose on one Linux host

This option deploys PostgreSQL, FastAPI and Next.js using `docker-compose.prod.yml`.

Piston remains a separate privileged container.

### Create the backend environment file

```bash
cp server/.env.example server/.env
```

Configure:

```env
JWT_SECRET=<generated-secret>
AI_PROVIDER_CHAIN=gemini,groq
GEMINI_API_KEY=<secret>
GROQ_API_KEY=<secret>

CORS_ORIGINS=https://app.example.com
RATE_LIMIT_ENABLED=true

STORAGE_BACKEND=local
LOCAL_STORAGE_DIR=uploads/resumes

CODE_EXECUTION_API_URL=http://host.docker.internal:2000/api/v2
CODE_EXECUTION_TIMEOUT_SECONDS=15
```

On Linux, `host.docker.internal` might require an explicit host-gateway mapping. A better long-term improvement is adding Piston to a dedicated Compose network and referring to it by an internal service name.

### Create the root Compose environment file

Create `.env` beside `docker-compose.prod.yml`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=ai_interview_copilot
NEXT_PUBLIC_API_URL=https://api.example.com
```

### Start Piston

```bash
docker volume create piston_data

docker run \
  --privileged \
  --volume piston_data:/piston \
  --detach \
  --restart unless-stopped \
  --publish 2000:2000 \
  --name piston_api \
  ghcr.io/engineer-man/piston
```

Install the runtime versions listed earlier.

### Build and start the application

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Inspect services:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f web
docker logs piston_api
```

Verify:

```bash
curl http://localhost:8000/health
curl -I http://localhost:3000
curl http://localhost:2000/api/v2/runtimes
```

### Reverse proxy

Neither application container terminates TLS. Put Caddy, Nginx or a managed load balancer in front.

Example Caddy configuration:

```caddyfile
app.example.com {
    reverse_proxy localhost:3000
}

api.example.com {
    reverse_proxy localhost:8000
}
```

Do not add a public reverse-proxy route for Piston.

### Stop the application

```bash
docker compose -f docker-compose.prod.yml down
```

This preserves named PostgreSQL and resume volumes.

To inspect volumes:

```bash
docker volume ls
```

Do not use `docker compose down -v` on a production host unless permanent deletion of database and upload volumes is explicitly intended.

## Database migrations

Every release that changes `server/alembic/versions/` requires:

```bash
cd server
alembic upgrade head
```

For Render, run this in the pre-deploy phase when possible.

For Docker Compose, the API command currently runs migrations before Uvicorn starts.

Before applying migrations to production:

1. Create a database backup.
2. Test the migration against a copy of production-like data.
3. Confirm upgrade-path data preservation.
4. Review destructive operations such as `drop_table`.
5. Document rollback or restore steps.
6. Apply the migration once.
7. Verify the application health check and critical workflows.

A fresh-database migration test does not prove that upgrades preserve existing data.

## Production CI and deployment behavior

The GitHub Actions workflow currently performs continuous integration.

On pushes and pull requests to `main`, it runs:

- backend pytest suite;
- fresh PostgreSQL migration test;
- frontend type checking;
- frontend linting;
- Next.js production build;
- API Docker image build;
- frontend Docker image build.

It does not directly deploy Vercel or Render.

Vercel and Render can independently connect to the GitHub repository and deploy after changes reach `main`. Configure Render to deploy only after CI checks pass.

The latest verified main-branch workflow is:

```text
CI #40
Commit: 900ff91
Result: successful
```

## Free-tier expectations

A personal demonstration can use:

- Vercel Hobby frontend;
- Render free backend;
- Render free PostgreSQL temporarily;
- AI-provider free quotas.

Limitations include:

- backend cold starts;
- 30-day Render PostgreSQL expiry;
- no free-database backups;
- ephemeral backend storage;
- limited service hours;
- AI-provider limits;
- no safe free Piston hosting guarantee.

Do not treat this arrangement as durable production storage.

## Production checklist

Before inviting real users:

- [ ] Latest GitHub Actions run is successful.
- [ ] Production database is persistent and backed up.
- [ ] Database migrations were tested with existing data.
- [ ] `JWT_SECRET` is unique and securely generated.
- [ ] AI secrets are stored only in platform secret settings.
- [ ] CORS contains only approved frontend origins.
- [ ] Rate limiting is enabled.
- [ ] Resume storage uses a private S3-compatible bucket.
- [ ] Piston is private, isolated and authenticated.
- [ ] Piston has all required runtimes installed.
- [ ] Code-execution quotas are enforced.
- [ ] Backend health checks are enabled.
- [ ] Error and external-provider failures are monitored.
- [ ] Account deletion and resume deletion are documented.
- [ ] Privacy and retention policies are published.
- [ ] Restore procedures have been tested.
- [ ] Preview deployments cannot access production data unintentionally.