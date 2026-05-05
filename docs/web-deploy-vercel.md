# Deploy VertiOne Web on Vercel

VertiOne Web must be deployed as a Vercel project whose root directory is `apps/web`.

## Vercel Settings

- Framework Preset: Next.js
- Root Directory: `apps/web`
- Node.js Version: 20.19 or newer
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: leave default

## Environment Variables

Configure these in Vercel for the web project:

- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`
- `NEXT_PUBLIC_API_BASE_URL`

`NEXT_PUBLIC_API_BASE_URL` should point to the protected backend base URL. Web API calls should use relative paths such as `/api/web/dashboard`.

## Backend Safety

Do not deploy the repository root as the Vercel root. Pointing Vercel at `apps/web` ensures:

- backend Docker files are ignored by the web build,
- Cloud Run deployment remains unchanged,
- Python dependencies and migrations are not part of the Vercel build.

## Deployment Split

Backend and web now deploy through separate paths:

- Cloud Run is deployed by GitHub Actions only when backend-relevant files change on `main`.
- Changes limited to `apps/web/**`, `docs/**`, or non-critical markdown files do not trigger the backend Cloud Run workflow.
- VertiOne Web should be deployed by Vercel with the project root set to `apps/web`.

The `apps/web/.vercelignore` file excludes local build artifacts and environment files from Vercel uploads.
