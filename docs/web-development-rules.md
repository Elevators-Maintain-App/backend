# VertiOne Web Development Rules

## Non-Negotiables

- Do not consume public legacy endpoints.
- Use `/api/web/*` by default.
- Do not add backend endpoints from frontend-only tasks.
- Do not change backend Docker files for web deployment.
- Do not change migrations unless the task explicitly includes backend persistence work.
- Preserve multi-company and role boundaries in every API contract.

## API Work

When a web feature needs backend data:

1. Define the screen contract first.
2. Prefer a dedicated `/api/web/*` endpoint.
3. Ensure Firebase ID tokens are sent as `Authorization: Bearer <token>`.
4. Keep service calls in `src/services`.
5. Validate forms with Zod and React Hook Form.
6. Use React Query for server state.

Do not call backend routes directly inside page components unless the call is trivial and still goes through a service wrapper.

## Auth and Roles

Web auth must mirror the mobile app profile lookup:

1. Firebase Auth login
2. Firestore `users/{uid}`
3. Read `data.rol`
4. Fallback to `data.role` only for compatibility
5. Normalize that Firestore value for routing and guards

Do not use Firebase custom claims as the primary role source in web.

Allowed roles are:

- `technician`
- `tecnico`
- `supervisor`
- `admin`
- `superAdmin`
- `super_admin`
- `client`
- `cliente`

Role normalization for web routing:

- `client` and `cliente` map to `/dashboard/client`
- `technician` and `tecnico` map to `/dashboard/technician`
- `supervisor` maps to `/dashboard/supervisor`
- `admin` maps to `/dashboard/admin`
- `superAdmin` and `super_admin` map to `/dashboard/superadmin`

Unknown roles must not be silently coerced. Route them to `/dashboard`, show the detected role, and keep logout visible.

If the Firestore document does not exist, show:

- `No se encontro documento de usuario en Firestore`

If the document exists but has no `rol` or `role`, show:

- `No se encontro rol en Firestore`

Use `RoleGuard` for route-level UX restrictions. Treat it as a frontend convenience only. Backend authorization remains mandatory.
Protected dashboard routes currently are:

- `/dashboard/client`
- `/dashboard/technician`
- `/dashboard/supervisor`
- `/dashboard/admin`
- `/dashboard/superadmin`

## UI

- Use shadcn/ui-compatible components from `src/components/ui`.
- Prefer VertiOne wrappers before raw primitives:
  - `AppButton`
  - `AppInput`
  - `AppCard`
  - `PageHeader`
  - `StatusBadge`
- Keep forms accessible with labels and clear validation messages.
- Avoid putting backend-specific formatting rules in React components.
- Keep layouts operational and dense enough for repeated internal use.
- Follow `docs/web-design-system.md` for color, spacing, typography and component behavior.

## Component Structure

- `src/components/ui`: design primitives and atomic wrappers.
- `src/components/forms`: reusable form controls with label, hint, error and accessibility wiring.
- `src/components/layout`: app shell, page headers and layout composition.
- `src/components/data-display`: tables, lists, metrics and data-focused components.
- `src/components/feedback`: empty, loading, error and status components.

Do not create feature-specific components in these folders. Feature-specific UI should live near the future module until a pattern repeats enough to promote it.

## Environment

Create `apps/web/.env.local` from `apps/web/.env.example` for local development.

Required variables:

- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`
- `NEXT_PUBLIC_API_BASE_URL`

Firebase config must use `NEXT_PUBLIC_*` names. The old mobile `EXPO_PUBLIC_*` names are not read by Next.js.

If Firebase configuration is missing, `src/lib/firebase.ts` must fail with a clear setup message naming the missing variables.

## Local Commands

Use Node.js 20.19 or newer.

```bash
cd apps/web
npm install
npm run dev
```

Use `npm run typecheck` and `npm run lint` before opening a PR.
