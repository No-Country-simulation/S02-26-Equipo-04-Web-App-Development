# Frontend PR Worklog

## Objetivo de la rama

Consolidar el flujo auth en Next.js y preparar una base de componentes reutilizables/documentacion para escalar frontend por dominio.

Rama de trabajo: `feature/frontend-next-auth-tokyo`.

## Cambios realizados

- Se rediseno `src/app/auth/login/page.tsx` con look Tokyo Night, panel lateral y formulario visual de acceso.
- Se rediseno `src/app/auth/register/page.tsx` con layout de onboarding, checklist visual y formulario base de registro.
- Se incorporaron iconos de `lucide-react` para reforzar jerarquia visual en inputs, CTAs y elementos informativos.
- Se mantuvieron redirecciones de rutas publicas (`getPublicOnlyRedirect`) y flujo demo de login hacia `/app`.
- Se agregaron animaciones coherentes con el tema usando clases y tokens existentes (`animate-fade-up`, `animate-drift`).
- Se creo `src/components/ui/Button.tsx` como primer componente reusable para estandarizar CTAs.
- Se migraron botones de submit en login/registro al nuevo componente reusable.
- Se centralizo redirect protegido en `src/app/app/layout.tsx` usando `getProtectedRedirect`.
- Se evito bootstrap redundante de sesion en login/registro chequeando `isBootstrapped`.
- Se actualizo `frontend/README.md` con arquitectura hibrida por dominio y reglas para juniors (incluye que NO conviene hacer).
- Se migraron `NavBar` y `Sidebar` desde `src/layouts/` hacia `src/components/layout/`.
- Se agrego un diagrama en arbol de carpetas dentro de `frontend/README.md` para visualizar la estructura objetivo.
- Se actualizo esta bitacora para reflejar el trabajo actual.

## Commits realizados

- `feat(frontend): redesign auth pages with tokyo night style`
- `docs(frontend): update worklog for auth redesign`
- `refactor(frontend): centralize protected redirect and auth bootstrap guard`
- `feat(frontend): add reusable button component for auth screens`
- `docs(frontend): update readmes with next architecture guidelines`

## Archivos clave

- `frontend/src/app/auth/login/page.tsx`
- `frontend/src/app/auth/register/page.tsx`
- `frontend/src/app/app/layout.tsx`
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/components/layout/README.md`
- `frontend/src/components/layout/NavBar.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/package.json`
- `frontend/README.md`
- `README.md`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run test` -> OK (5 tests)
- `npm run build` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] `npm run test` OK
- [x] `npm run build` OK
- [x] Documentacion actualizada

## Actualizacion 2026-02-16 (logo + navbar)

- Rama de trabajo: `feature/frontend-logo-navbar-home`.
- Se agrego `frontend/src/components/branding/HaceloCortoLogo.tsx` con 4 variantes (`icon`, `compact`, `wordmark`, `wordmarkMono`) y paleta editable por props para cambiar colores sin tocar el SVG base.
- Se integro el logo compacto en la barra superior de dashboard (`frontend/src/components/layout/NavBar.tsx`) y en la barra superior de landing (`frontend/src/app/page.tsx`).
- El logo de dashboard ahora funciona como acceso rapido al home (`/`).
- Se corrigio la visibilidad del boton hamburguesa para que solo aparezca en mobile/tablet y no en desktop.
- Se ajusto `frontend/src/components/layout/Sidebar.tsx` para dejar el sidebar fijo solo en desktop (`lg`) y mantener comportamiento de panel desplegable en mobile/tablet.
- En desktop se muestra la variante `wordmark` (icono + nombre), mientras que en mobile/tablet se mantiene `compact`.

## Actualizacion 2026-02-18 (video upload + settings + preview)

- Rama de trabajo: `feature/frontend-video-upload-settings-preview`.
- Se conecto el upload real de video desde `frontend/src/app/app/page.tsx` usando el nuevo servicio `frontend/src/services/videoApi.ts` y se removio el delay/mock anterior.
- Se incorporo la accion para solicitar la URL de descarga presignada y mostrarla desde el panel de estado (`frontend/src/components/home/ProjectStatusPanel.tsx`).
- Se rehizo el modal de ajustes de video para ubicarlo dentro de `home`, alineado al estilo visual existente, en `frontend/src/components/home/VideoSettingsModal.tsx`.
- Se agrego persistencia de settings en `frontend/src/store/useVideoSettingsStore.ts` (zustand + persist).
- Se elimino el modal anterior fuera de lugar: `frontend/src/components/layout/ModalSetings.tsx`.
- Se agrego mini preview del video subido en el panel de estado; cuando el upload finaliza, reemplaza visualmente el bloque de progreso.

### Commits realizados (rama actual)

- `feat(frontend): connect upload flow with video endpoints`
- `feat(frontend): add and persist home video settings modal`
- `feat(frontend): show mini preview after video upload`
- `docs(frontend): log video upload and settings work`

### Validaciones locales (rama actual)

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run test` -> OK (9 tests)
- `npm run build` -> OK
