# AI Interview Copilot — Frontend

The frontend for AI Interview Copilot, an AI-powered interview-preparation platform that provides role-specific resume analysis, personalized mock interviews, coding exercises, performance feedback, and learning roadmaps.

This application is built with Next.js, React, TypeScript, Tailwind CSS, Radix UI, shadcn/ui, and Monaco Editor. It communicates with the FastAPI backend through a configurable public API URL.

## Features

- User registration and authentication
- Automatic access-token refresh
- Protected application routes
- Resume upload and role-specific ATS analysis
- Personalized interview sessions
- Behavioral, technical, and coding interview rounds
- Monaco-based code editor
- Code execution and test-case results
- Interview scoring and detailed feedback
- Previous resume and interview history
- Personalized learning roadmaps
- Light and dark themes
- Responsive interface
- Production-ready standalone Next.js build

## Technology stack

| Category | Technology |
| --- | --- |
| Framework | Next.js 16 |
| UI library | React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS 4 |
| Components | Radix UI and shadcn/ui |
| Code editor | Monaco Editor |
| Icons | Lucide React |
| Linting | ESLint |
| Deployment | Vercel or Docker |

## Prerequisites

Install the following before running the frontend:

- Node.js 20 or later
- npm
- A running AI Interview Copilot backend

The backend runs at `http://localhost:8000` by default.

For complete backend, PostgreSQL, AI-provider, and Piston setup instructions, see the repository root `README.md` and `docs/DEPLOYMENT.md`.

## Local development

From the repository root, enter the frontend directory:

```bash
cd client
```

Install dependencies:

```bash
npm ci
```

Create the local environment file.

macOS or Linux:

```bash
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\n' > .env.local
```

Windows PowerShell:

```powershell
Set-Content .env.local "NEXT_PUBLIC_API_URL=http://localhost:8000"
```

Start the development server:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

The backend should be available at:

```text
http://localhost:8000
```

## Environment variables

The frontend uses one public environment variable:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Recommended | `http://localhost:8000` | Public base URL of the FastAPI backend |

Example for local development:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Example for production:

```env
NEXT_PUBLIC_API_URL=https://api.example.com
```

Variables prefixed with `NEXT_PUBLIC_` are included in the browser bundle. Never store API keys, database credentials, JWT secrets, or other sensitive values in these variables.

`NEXT_PUBLIC_API_URL` is embedded during the Next.js build. Rebuild or redeploy the frontend after changing it.

## Available commands

| Command | Description |
| --- | --- |
| `npm run dev` | Start the Next.js development server |
| `npm run build` | Create a production build |
| `npm run start` | Start the production server |
| `npm run lint` | Run ESLint |
| `npx tsc --noEmit` | Run TypeScript validation without generating files |

Before committing frontend changes, run:

```bash
npx tsc --noEmit
npm run lint
npm run build
```

## Application routes

| Route | Access | Purpose |
| --- | --- | --- |
| `/` | Public | Product landing page |
| `/register` | Public | Create a user account |
| `/login` | Public | Authenticate an existing user |
| `/dashboard` | Protected | View resumes and interview sessions |
| `/resume/new` | Protected | Upload and analyze a resume |
| `/resume/[resumeId]` | Protected | View resume analysis and start an interview |
| `/interview/[sessionId]` | Protected | Complete an interview and review results |

After successful registration, users are redirected to `/login`. Registration does not automatically authenticate the new account.

After successful login, users are redirected to `/dashboard`.

Unauthenticated users who visit protected routes are redirected to `/login`.

## Frontend structure

```text
client/
├── app/
│   ├── dashboard/
│   │   └── page.tsx
│   ├── interview/
│   │   └── [sessionId]/
│   │       └── page.tsx
│   ├── login/
│   │   └── page.tsx
│   ├── register/
│   │   └── page.tsx
│   ├── resume/
│   │   ├── [resumeId]/
│   │   │   └── page.tsx
│   │   └── new/
│   │       └── page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/
│   ├── code-editor.tsx
│   ├── nav-bar.tsx
│   ├── protected-route.tsx
│   ├── score-list.tsx
│   ├── score-ring.tsx
│   ├── test-case-results.tsx
│   └── theme-toggle.tsx
├── lib/
│   ├── api.ts
│   ├── auth-context.tsx
│   ├── theme-context.tsx
│   ├── types.ts
│   └── utils.ts
├── public/
├── scripts/
│   └── copy-monaco-assets.js
├── Dockerfile
├── components.json
├── eslint.config.mjs
├── next.config.ts
├── package.json
├── postcss.config.mjs
└── tsconfig.json
```

## API integration

All backend requests are centralized in `lib/api.ts`.

The API client supports:

- User registration
- Login and logout
- Access-token refresh
- Current-user retrieval
- Resume upload and analysis
- Resume history
- Starting interview sessions
- Submitting interview answers
- Running code
- Completing interviews
- Interview-session history and details

The API base URL is resolved using:

```ts
process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
```

Do not hard-code deployment URLs in individual components. Use `NEXT_PUBLIC_API_URL`.

## Authentication flow

Authentication is managed by `lib/auth-context.tsx` and `lib/api.ts`.

The current flow is:

1. The user registers.
2. The frontend redirects the user to `/login`.
3. The user submits their email and password.
4. The backend returns access and refresh tokens.
5. The frontend stores the tokens in browser local storage.
6. Authenticated API requests include the access token.
7. When an access token expires, the frontend attempts one refresh operation.
8. If refresh fails, local authentication state is cleared.
9. Protected routes redirect the user to `/login`.

Local-storage token handling is practical for the current personal-project architecture. For a security-hardened commercial SaaS, consider migrating refresh tokens to `HttpOnly`, `Secure`, and `SameSite` cookies so browser JavaScript cannot read them.

## Monaco Editor assets

The coding interface uses Monaco Editor.

The `postinstall` script copies required Monaco assets into the public directory:

```json
"postinstall": "node scripts/copy-monaco-assets.js"
```

This runs automatically after a normal dependency installation:

```bash
npm install
```

The production Docker build installs dependencies without lifecycle scripts and then runs the asset-copying script explicitly after the full source tree is available.

If the editor loads without workers or syntax support, run:

```bash
node scripts/copy-monaco-assets.js
```

Then restart the development server.

## Production build

Create a production build:

```bash
npm ci
npm run build
```

Start the production server:

```bash
npm run start
```

The Next.js configuration uses standalone output:

```ts
const nextConfig = {
  output: "standalone",
};
```

Standalone output produces a smaller deployment artifact suitable for containerized environments.

## Docker

Build the frontend image from the repository root:

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
  -t ai-interview-copilot-web \
  ./client
```

Windows PowerShell:

```powershell
docker build `
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com `
  -t ai-interview-copilot-web `
  ./client
```

Run the image:

```bash
docker run --rm -p 3000:3000 ai-interview-copilot-web
```

Open:

```text
http://localhost:3000
```

The image:

- Uses Node.js 20
- Installs dependencies with `npm ci`
- Copies Monaco Editor assets
- Creates a standalone Next.js build
- Runs as a non-root user
- Exposes port `3000`
- Includes an HTTP health check

Because `NEXT_PUBLIC_API_URL` is compiled into the browser bundle, provide it as a build argument. Setting it only when starting the container will not update the already-built frontend.

## Deploying to Vercel

1. Import the GitHub repository into Vercel.
2. Set the root directory to:

   ```text
   client
   ```

3. Keep the detected framework as Next.js.
4. Add the production environment variable:

   ```env
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   ```

5. Deploy the project.
6. Copy the final Vercel frontend URL.
7. Add that URL to the backend’s allowed origins:

   ```env
   CORS_ORIGINS=https://your-project.vercel.app
   ```

8. Redeploy the backend if its environment configuration changed.
9. Redeploy the frontend whenever `NEXT_PUBLIC_API_URL` changes.

Do not add backend secrets to Vercel’s frontend environment.

## Continuous integration

GitHub Actions validates the frontend on pushes and pull requests targeting `main`.

The frontend CI job performs:

```bash
npm ci
npx tsc --noEmit
npm run lint
npm run build
```

A change should not be merged or deployed until these checks pass.

## Backend CORS configuration

The browser calls the FastAPI backend directly. The backend must allow the frontend’s exact origin.

Local development:

```env
CORS_ORIGINS=http://localhost:3000
```

Production:

```env
CORS_ORIGINS=https://your-project.vercel.app
```

For multiple explicitly trusted origins:

```env
CORS_ORIGINS=https://app.example.com,https://preview.example.com
```

Avoid using a wildcard origin for authenticated production requests.

## Troubleshooting

### The frontend cannot reach the backend

Verify that `.env.local` contains:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Confirm that the backend health endpoint works:

```bash
curl http://localhost:8000/health
```

Restart the development server after changing `.env.local`.

### Requests are blocked by CORS

Confirm that the frontend origin is included in the backend’s `CORS_ORIGINS`.

The origin must match the browser URL exactly, including:

- Protocol
- Hostname
- Port, when applicable

For example, `http://localhost:3000` and `http://127.0.0.1:3000` are different origins.

### Registration succeeds but the user is not logged in

This is expected behavior. Successful registration redirects the user to `/login`, where they must authenticate using the newly created account.

### Protected pages redirect to login

Possible causes include:

- No stored access token
- Expired access and refresh tokens
- The backend is unavailable
- The `/auth/me` request failed
- The backend rejected the token

Log in again and inspect the browser’s network panel if the problem continues.

### Environment changes do not appear in production

`NEXT_PUBLIC_API_URL` is embedded during the build. Trigger a new frontend deployment after changing it.

### Monaco Editor does not load correctly

Reinstall dependencies or manually copy the editor assets:

```bash
npm ci
node scripts/copy-monaco-assets.js
```

Then restart the application.

### The production build fails

Run the validation commands separately:

```bash
npx tsc --noEmit
npm run lint
npm run build
```

Resolve the first reported error before retrying the complete build.

## Security considerations

- Never place secrets in `NEXT_PUBLIC_*` variables.
- Do not commit `.env.local`.
- Allow only trusted frontend origins in backend CORS settings.
- Serve production traffic over HTTPS.
- Avoid rendering untrusted HTML.
- Keep Next.js and frontend dependencies updated.
- Treat browser local storage as accessible to JavaScript running on the same origin.
- Do not expose AI-provider keys or Piston credentials to the browser.
- Send all privileged operations through the backend.

## Accessibility and interface quality

When modifying the interface:

- Use semantic HTML.
- Associate labels with form fields.
- Preserve keyboard navigation.
- Maintain visible focus states.
- Provide meaningful loading and error states.
- Check color contrast in light and dark themes.
- Test layouts at mobile and desktop widths.
- Avoid relying on color alone to communicate status.

## Contribution workflow

1. Create a branch from `main`.
2. Make the frontend changes.
3. Run:

   ```bash
   npx tsc --noEmit
   npm run lint
   npm run build
   ```

4. Review the affected pages manually.
5. Commit using a conventional commit message.
6. Push the branch and open a pull request.
7. Wait for CI to pass before merging.

Example commit messages:

```text
feat(client): add interview progress indicator
fix(auth): redirect registered users to login
fix(editor): handle Monaco worker loading failure
refactor(api): centralize interview request handling
docs(client): document frontend setup and deployment
```

## Related documentation

- Root project guide: `../README.md`
- Production deployment: `../docs/DEPLOYMENT.md`
- System architecture: `../docs/system-design.md`
- Frontend container: `Dockerfile`
- Backend environment reference: `../server/.env.example`

## License

No repository license is currently included. Add a license only after deciding how other people may use, modify, and distribute the project.