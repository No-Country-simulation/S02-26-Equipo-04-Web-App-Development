# Frontend + Backend PR Worklog

## Objetivo de la rama

Implementar un flujo mas liviano para upload de videos: obtener metadata basica en frontend antes de subir, enviarla en el mismo request, y evitar procesamiento pesado de video en el nodo `/api`.

Rama de trabajo: `feature/frontend-worker-metadata-preview`.

## Cambios realizados

- Se actualizo el flujo de Home para leer metadata del archivo local al seleccionarlo (`duration`, `width`, `height`) con `HTMLVideoElement` y `onloadedmetadata`.
- Se agrego fallback por timeout/error para que el upload continue aunque el navegador no pueda resolver metadata del archivo.
- Se extendio `videoApi.upload(...)` para enviar metadata opcional en `multipart/form-data` junto al archivo (`duration_seconds`, `width`, `height`, `fps`).
- El endpoint `POST /api/v1/videos/upload` ahora acepta esa metadata opcional via `Form`.
- Se agrego normalizacion de campos numericos en API (`duration_seconds` y `fps`) para persistir valores enteros seguros.
- Se elimino en API el uso de `ffprobe` durante upload (extraccion pesada de metadata en tiempo de request).
- Se incorporo `ClientVideoMetadata` como schema de validacion para metadata inicial enviada por frontend.
- Se agrego persistencia de metadata inicial en `VideoService` sin ejecutar tareas de video/audio pesadas en `/api`.
- Se desactivo por defecto el analisis pesado de medios en API durante auto-clips (`ffprobe`/`ffmpeg`) mediante flag de configuracion.
- El servicio de jobs ahora prioriza metadata ya persistida (`video.duration_seconds`) y, si el flag esta desactivado, evita fallback de probe en `/api`.
- Se agrego cache local de video fuente en worker para reutilizar descargas entre jobs del mismo video y reducir I/O de red repetido.
- Se optimizo el loop del worker para evitar consultas duplicadas de `Video` por job y se removio la generacion de URL publica no utilizada tras el upload del clip.

## Commits realizados

- `feat(upload): move initial video metadata capture to frontend`
- `refactor(api): disable heavy media analysis in auto-clips by default`
- `perf(worker): cache source videos locally across reframe jobs`
- `perf(worker): reduce redundant video reads and skip unused public url generation`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/services/videoApi.ts`
- `backend/api/app/api/v1/endpoints/video.py`
- `backend/api/app/services/video_service.py`
- `backend/api/app/schemas/video.py`
- `backend/api/app/services/job_service.py`
- `backend/api/app/core/config.py`
- `backend/worker/app/worker.py`
- `docs/front_back-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

Ejecutado en raiz del repo:

- `python3 -m py_compile backend/api/app/api/v1/endpoints/video.py backend/api/app/services/video_service.py backend/api/app/schemas/video.py` -> OK
- `python3 -m py_compile backend/api/app/services/job_service.py backend/api/app/core/config.py` -> OK
- `python3 -m py_compile backend/worker/app/worker.py` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Cambios de frontend para metadata previa al upload
- [x] Cambios de backend para recibir/persistir metadata sin `ffprobe` en API
- [x] Analisis pesado de auto-clips desactivado por defecto en `/api`
- [x] Cache local de source video en worker para evitar descargas repetidas
- [x] Validaciones locales ejecutadas
- [x] Worklog front+back actualizado solo con el alcance de esta rama
