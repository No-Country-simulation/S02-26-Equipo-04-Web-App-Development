# Frontend PR Worklog

## Objetivo de la rama

Migrar `frontend/` desde Vite a Next.js `16.1.6`, mantener Tailwind CSS en `4.1.x`, y dejar CI + documentacion alineados con el nuevo stack.

Rama de trabajo: `feature/frontend-next16-tailwind41`.

## Cambios realizados

- Se reemplazo el toolchain de Vite por Next.js (`next dev`, `next build`, `next start`).
- Se migro el entrypoint a App Router con `app/layout.tsx`, `app/page.tsx` y `app/not-found.tsx`.
- Se removio React Router y se adaptaron rutas/links al modelo de Next.
- Se migro Tailwind a `4.1.x` con plugin oficial `@tailwindcss/postcss` y tema en `@theme` dentro de `app/globals.css`.
- Se separo la configuracion de pruebas a `vitest.config.ts` para mantener tests sin dependencia de Vite.
- Se limpiaron archivos legacy de Vite (`index.html`, `vite.config.ts`, `tailwind.config.ts`, `src/main.tsx`, `src/router.tsx`, etc.).
- Se actualizo la guia de workflow para versionar `docs/frontend-pr-log.md`.
- Se quito `docs/frontend-pr-log.md` del `.gitignore` para que la bitacora viaje con la rama.

## Commits realizados

- `chore(frontend): migrate frontend from vite to next 16.1.6`
- `docs(frontend): track next migration in frontend worklog`

## Archivos clave

- `frontend/package.json`
- `frontend/next.config.ts`
- `frontend/tsconfig.json`
- `frontend/eslint.config.js`
- `frontend/postcss.config.mjs`
- `frontend/vitest.config.ts`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/not-found.tsx`
- `frontend/app/globals.css`
- `.github/workflows/frontend-ci.yml`
- `.gitignore`
- `docs/frontend-git-workflow.md`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run test` -> OK (1 test)
- `npm run build` -> OK
- `npm run dev -- --hostname 0.0.0.0 --port 4173` -> OK (arranca en local)

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] `npm run test` OK
- [x] `npm run build` OK
- [x] Documentacion actualizada
