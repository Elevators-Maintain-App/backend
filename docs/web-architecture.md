# VertiOne Web Architecture

VertiOne Web lives in `apps/web` as an isolated Next.js application inside the backend repository. It must not change backend runtime behavior, Docker images, migrations, or existing FastAPI routes.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Firebase Auth
- React Query
- Axios
- Zod
- React Hook Form
- shadcn/ui conventions

## Directory Layout

- `apps/web/src/app`: App Router routes and layouts.
- `apps/web/src/components`: Shared React components.
- `apps/web/src/components/ui`: shadcn/ui-compatible primitives.
- `apps/web/src/lib`: Infrastructure helpers such as Firebase and Axios clients.
- `apps/web/src/services`: API service functions.
- `apps/web/src/hooks`: Shared hooks.
- `apps/web/src/types`: Shared TypeScript types.

## Auth Model

The web app authenticates with Firebase Auth. `AuthProvider` listens to Firebase token changes and builds a minimal local profile from token claims:

- `uid`
- `email`
- `displayName`
- `role`
- `companyId`

The backend remains the source of operational data and authorization. Frontend role guards are only a UX boundary; backend endpoints must enforce role, company, and resource permissions.

## API Boundary

New web screens must use:

- `/api/web/*` endpoints, or
- explicitly approved protected core endpoints.

The default Axios client rejects absolute URLs and rejects relative paths that do not start with `/api/web/`. If a protected core endpoint is intentionally approved, update the allowed prefixes in `apps/web/src/lib/api-client.ts` together with contract documentation.

Legacy public endpoints must not be used by VertiOne Web.

## Backend Isolation

This scaffold intentionally does not modify:

- `app/`
- `migrations/`
- backend `Dockerfile`
- backend `docker-compose.yml`
- existing FastAPI route behavior

Vercel should build only `apps/web`.
