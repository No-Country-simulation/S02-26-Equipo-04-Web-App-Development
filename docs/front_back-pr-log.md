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

## Commits realizados

- `feat(upload): move initial video metadata capture to frontend`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/services/videoApi.ts`
- `backend/api/app/api/v1/endpoints/video.py`
- `backend/api/app/services/video_service.py`
- `backend/api/app/schemas/video.py`
- `docs/front_back-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

Ejecutado en raiz del repo:

- `python3 -m py_compile backend/api/app/api/v1/endpoints/video.py backend/api/app/services/video_service.py backend/api/app/schemas/video.py` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Cambios de frontend para metadata previa al upload
- [x] Cambios de backend para recibir/persistir metadata sin `ffprobe` en API
- [x] Validaciones locales ejecutadas
- [x] Worklog front+back actualizado solo con el alcance de esta rama
