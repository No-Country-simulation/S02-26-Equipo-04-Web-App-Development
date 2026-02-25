# Frontend PR Worklog

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feat/frontend-google-login`

### Objetivo

Conectar el flujo de login/registro del frontend con Google OAuth del backend y cerrar el circuito de callback para iniciar sesion real.

### Cambios implementados en curso

- Se activaron los botones de Google en `frontend/src/app/auth/login/page.tsx` y `frontend/src/app/auth/register/page.tsx` para pedir la URL de OAuth al backend, guardar `state` en `sessionStorage` y redirigir al proveedor.
- Se agregaron metodos en `frontend/src/services/authApi.ts` para `getGoogleAuthUrl` y `googleCallback`.
- Se incorporo `completeGoogleAuth` en `frontend/src/store/useAuthStore.ts` para cerrar sesion local de forma consistente con login/register por email.
- Se creo la pantalla `frontend/src/app/auth/callback/page.tsx` para validar `code/state`, ejecutar el callback contra backend y redirigir a `/app` al autenticar.
- Se corrigio la pantalla de callback para evitar falsos negativos de `state invalido` en desarrollo (doble ejecucion de efectos por `reactStrictMode`) procesando cada `code` una sola vez y limpiando `sessionStorage` al finalizar autenticacion.
- Se ajusto la ruta `auth/callback` para produccion (Next 16): se separo en componente cliente + `Suspense` en `page.tsx`, evitando el error de build por `useSearchParams()` fuera de boundary.

### Commits de esta rama (frontend)

- `feat(frontend): integrate google oauth login and callback flow`
- `docs(worklog): update frontend log and add backend handoff notes`

### Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Objetivo de la rama

Retirar de la vista de estado del proyecto las acciones de descarga (obtener URL y descargar video) para reutilizarlas despues en otra pantalla, manteniendo la UI actual limpia y enfocada.

Rama de trabajo: `feat/frontend-extract-download-actions`.

## Cambios realizados

- Se extrajeron los botones de `Obtener URL de descarga` y `Descargar video subido` desde `frontend/src/components/home/ProjectStatusPanel.tsx` para que ya no se muestren en la seccion de estado del proyecto.
- Se creo el componente reutilizable `frontend/src/components/home/DownloadVideoActions.tsx` con la logica de resolucion de URL y accion de descarga para uso futuro en otra vista.
- Se simplifico `frontend/src/app/app/page.tsx` removiendo estado y props de descarga que ya no corresponden a esta pantalla (`downloadData`, `downloadError`, `isResolvingDownloadUrl`, `handleResolveDownloadUrl`).
- Se mantuvo el flujo de upload y preview sin cambios visuales fuera del panel de estado.

## Commits realizados

- `feat(frontend): move download actions out of project status panel`
- `docs(frontend): update PR log for download actions extraction`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/components/home/ProjectStatusPanel.tsx`
- `frontend/src/components/home/DownloadVideoActions.tsx`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] Documentacion actualizada

## Objetivo de la rama

Integrar sobre `develop` actualizado el flujo completo de timeline + biblioteca (frontend/backend) para dejar operativas las vistas de clips/videos, acciones CRUD, navegacion de edicion profunda y ruta de compartir.

Rama de trabajo: `feature/integracion-timeline-library-flow`.

## Cambios realizados

- Se integraron en `frontend/src/app/app/page.tsx` y `frontend/src/components/home/GeneratedClipsSection.tsx` las mejoras de Home para jobs automaticos, persistencia de draft, polling estable y transiciones de preview.
- Se incorporo `frontend/src/app/app/timeline/page.tsx` con editor manual conectado al endpoint de reframe, incluyendo seleccion de clip/video, paginacion y busqueda contra backend.
- Se amplió `frontend/src/app/app/library/page.tsx` con vistas de `Clips` y `Videos originales`, mas acciones de renombrar/eliminar para videos y editar/compartir/eliminar para clips.
- Se agrego `frontend/src/app/app/share/[clipId]/page.tsx` para preparar el flujo de compartir por red social y se fortalecio el deep-link de `Editar` hacia timeline por `clipId`/`videoId`.
- Se actualizaron servicios en `frontend/src/services/videoApi.ts` para soportar listados paginados/buscables, CRUD de videos y clips, y creacion de jobs manuales/automaticos.
- Se aplico refresh visual en dashboard (`frontend/src/app/globals.css`, `frontend/src/components/branding/HaceloCortoLogo.tsx`, `frontend/src/components/layout/NavBar.tsx`) con paleta Catppuccin y correccion de navegacion del logo.

## Commits realizados

- `feat(frontend): wire home upload flow to auto reframe jobs endpoint`
- `feat(frontend): move preview workflow to timeline and fetch user clips`
- `feat(frontend): add backend search and original videos library view`
- `feat(frontend): wire timeline editor to manual reframe endpoint`
- `feat(frontend): add rename and delete actions to library videos`
- `feat(frontend): add clip share route and stronger timeline edit deep-link`
- `style(frontend): switch dashboard palette to catppuccin and fix home logo link`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/app/app/library/page.tsx`
- `frontend/src/app/app/share/[clipId]/page.tsx`
- `frontend/src/services/videoApi.ts`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Integracion de cambios frontend/backend de `feature/frontend-backend-timeline-library-flow`
- [x] `npm run lint` OK
- [x] Documentacion actualizada

## Objetivo de la rama

Ajustar el frontend a cambios recientes de backend en `develop`, priorizando estabilidad del flujo de timeline (crear clips y guardar nombre de video).

Rama de trabajo: `feature/frontend-sync-upload-develop`.

## Cambios realizados

- Se alineo el timeline con la validacion actual de backend (duracion minima de 5s por clip) en `frontend/src/app/app/timeline/page.tsx` y `frontend/src/components/home/videoPrevewTimeLine/useVideoTrim.ts`.
- Se reforzo el panel de ajustes en `frontend/src/components/home/VideoSettings.tsx` mostrando duracion estimada, minimo permitido y bloqueo del boton cuando el recorte no cumple reglas.
- Se corrigio guardado de nombre en timeline para usar el `selectedVideoId` real y refrescar listado local luego de editar filename.
- Se corrigio manejo de error en guardado de nombre para mostrar el mensaje real del backend en lugar de estado previo.
- Se eliminaron warnings de lint pendientes en timeline/settings para mantener baseline limpia.

## Commits realizados

- `fix(frontend): align timeline clip creation with backend constraints`
- `docs(frontend): log timeline compatibility updates on develop sync`

## Archivos clave

- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/components/home/VideoSettings.tsx`
- `frontend/src/components/home/videoPrevewTimeLine/useVideoTrim.ts`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run test -- --run` -> OK
- `npm run build` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] `npm run test` OK
- [x] `npm run build` OK
- [x] Documentacion actualizada
