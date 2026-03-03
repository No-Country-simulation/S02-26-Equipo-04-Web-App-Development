# Backend PR Worklog

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feature/mi-tarea`

### Objetivo

Hacer que los resultados de mezcla de audio (`ADD_AUDIO`) aparezcan en Biblioteca como clips del usuario, igual que los `REFRAME`.

### Contexto y por que se hizo

- Antes de este ajuste, el endpoint `GET /api/v1/jobs/my-clips` filtraba solo `JobType.REFRAME`.
- El flujo de Audio Editor genera jobs `JobType.ADD_AUDIO`, por lo que esos resultados quedaban fuera de la consulta de biblioteca aunque el archivo final existiera en MinIO y el `output_path` estuviera guardado.
- Efecto visible en frontend: el usuario ve que la mezcla termina y existe en storage, pero no aparece en `Biblioteca > Clips`.
- Tambien habia inconsistencia funcional: aunque un job `ADD_AUDIO` se mostrara por otras vias, `GET /api/v1/jobs/{job_id}` y `DELETE /api/v1/jobs/{job_id}` estaban restringidos a `REFRAME`, dejando acciones incompletas para ese tipo.
- Agregar `job_type` al schema de salida permite a frontend etiquetar correctamente el origen del clip y evita tratar un mix de audio como si fuera un reframe comun.

### Cambios implementados en curso

- Se actualizo `backend/api/app/services/job_service.py` para que `GET /api/v1/jobs/my-clips` incluya jobs `REFRAME` y `ADD_AUDIO` cuando tienen `output_path`.
- Se ajusto `GET /api/v1/jobs/{job_id}` y `DELETE /api/v1/jobs/{job_id}` para aceptar ambos tipos (`REFRAME` y `ADD_AUDIO`) manteniendo ownership checks.
- Se agrego `job_type` en `UserClipItem` (`backend/api/app/schemas/job.py`) para que frontend pueda diferenciar visualmente el origen del clip.
- En la iteracion de `Share > YouTube + IA` no se requirieron cambios adicionales de API: frontend consume el endpoint ya disponible `GET /api/v1/youtube/metadata/{job_id}` y solo se reforzo documentacion para explicar el motivo de los ajustes previos.

### Commits de esta rama (backend)

- `feat(backend): include add-audio jobs in user clips endpoints`

### Validaciones locales

- `docker exec fastapi python -m compileall app` -> OK

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feat/backend-youtube-ai-metadata`

### Objetivo

Agregar sugerencias automaticas de metadata para YouTube (titulo, descripcion, hashtags y tags) desde backend, con fallback seguro y opcion IA via OpenRouter.

### Cambios implementados en curso

- Se agrego `GET /api/v1/youtube/metadata/{job_id}` en `backend/api/app/api/v1/endpoints/youtube.py` para devolver metadata sugerida por clip autenticado.
- Se extendio `backend/api/app/schemas/youtube.py` con `YouTubeMetadataSuggestionResponse` (`title`, `description`, `hashtags`, `tags`, `provider`, `generated_with_ai`).
- Se implemento en `backend/api/app/services/youtube_upload_service.py` la logica de sugerencia de copy usando como contexto:
  - `source_filename` del video original,
  - extracto de subtitulos si existe (`output_path.subtitles`),
  - `job_id`,
  - `tone` recibido desde frontend (`neutral`, `energetic`, `informative`).
- Se enforcean limites y normalizacion post-modelo para asegurar salida publicable:
  - `title <= 100`, `description <= 5000`,
  - limpieza y dedupe de hashtags/tags,
  - JSON estricto con fallback robusto si la respuesta IA viene en formato no ideal.
- Se agrego fallback deterministico cuando no hay key o falla provider IA (`provider=template`, `generated_with_ai=false`) para no bloquear publicacion.
- Se agregaron variables opcionales en `backend/api/app/core/config.py` y `backend/api/.env.example`:
  - `OPENROUTER_API_KEY`,
  - `OPENROUTER_MODEL` (ej: `arcee-ai/trinity-large-preview:free`),
  - `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`.

### Commits de esta rama (backend)

- `feat(backend): add youtube metadata suggestion endpoint`
- `feat(backend): add tone control for youtube metadata suggestions`
- `docs(backend): document youtube ai metadata flow and env setup`

### Validaciones locales

- `python3 -m compileall backend/api/app/api/v1/endpoints/youtube.py backend/api/app/services/youtube_upload_service.py` -> OK
- Verificacion manual de `GET /api/v1/youtube/metadata/{job_id}`:
  - sin key -> responde fallback `template`,
  - con key -> responde `provider=openrouter:<model>` cuando IA responde correctamente.

## Objetivo

Dejar documentado, paso a paso, que cambios necesita backend para que el login con Google funcione estable en local y no rompa el flujo de `/auth/callback` en frontend.

## Resumen del problema observado

- OAuth con Google llegaba a devolver `code` correctamente.
- El callback backend devolvia token, pero luego `/api/v1/auth/me` caia en `500`.
- Error SQL: se intentaba buscar `users.id` con un email (`invalid input syntax for type uuid`).

## Causa raiz

En OAuth Google se estaba emitiendo JWT con `sub = user.email`, pero el backend valida el token asumiendo `sub = user.id` (UUID):

- Emision token (OAuth): `backend/api/app/services/google_oauth_service.py`
- Lectura token (`get_current_user`): `backend/api/app/core/dependencies.py`

## Solucion aplicada en local

### 1) Unificar el `sub` del JWT en OAuth

- Archivo: `backend/api/app/services/google_oauth_service.py`
- Reemplazo:
  - Antes: `create_access_token(subject=user.email)`
  - Despues: `create_access_token(subject=str(user.id))`

Por que: mantiene la misma convencion que login/register tradicional (`sub` con UUID).

### 2) Agregar compatibilidad temporal para tokens viejos

- Archivo: `backend/api/app/core/dependencies.py`
- Cambio en `get_current_user`:
  - Primero intenta parsear `token_data.sub` como UUID y buscar por `User.id`.
  - Si no es UUID, cae en fallback y busca por `User.email`.

Por que: evita `500` cuando hay tokens antiguos emitidos con email en `sub`.

## Cambios de configuracion local (solo para pruebas)

### A) Variables OAuth de Google

- Archivo: `backend/api/.env`
- Agregar:
  - `GOOGLE_CLIENT_ID=<client_id_real>`
  - `GOOGLE_CLIENT_SECRET=<client_secret_real>`
  - `GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback`

### B) No pisar credenciales con `dev` en compose

- Archivo: `backend/docker-compose.yml`
- Quitar o comentar en `api.environment`:
  - `GOOGLE_CLIENT_ID=dev`
  - `GOOGLE_CLIENT_SECRET=dev`

Si quedan hardcodeadas en compose, pisan `.env` y Google responde `invalid_client`.

## Flujo de validacion sugerido para un jr backend

1. Cargar credenciales reales en `backend/api/.env`.
2. Verificar que `backend/docker-compose.yml` no sobreescriba con `dev`.
3. Levantar backend:
   - `docker compose up -d --build api`
4. Probar login Google desde frontend en `http://localhost:3000/auth/login`.
5. En logs backend, verificar:
   - `POST /api/v1/auth/google/callback` -> 200
   - `GET /api/v1/auth/me` -> 200

## Nota de seguridad

- Nunca commitear `client_secret` real en el repo.
- Si un secreto se filtra en chats/capturas, rotarlo en Google Cloud inmediatamente.

## Objetivo de la rama

Integrar sobre `develop` actualizado los cambios de backend que habilitan flujo completo de timeline/biblioteca: jobs automaticos y manuales, busqueda/listados paginados, y CRUD autenticado de videos/clips.

Rama de trabajo: `feature/integracion-timeline-library-flow`.

## Cambios implementados

- Se estabilizo el worker (`backend/worker/app/pipeline.py`, `backend/worker/app/worker.py`) y el flujo de procesamiento para mejorar consistencia de salida.
- Se incorporo en jobs el flujo de autoclips y listado de clips del usuario en `backend/api/app/api/v1/endpoints/job.py` y `backend/api/app/services/job_service.py`.
- Se agrego soporte de filtros opcionales para reframe manual en `backend/api/app/schemas/job.py`, endpoint y servicio de jobs.
- Se mejoro `GET /api/v1/jobs/status/{job_id}` y `GET /api/v1/jobs/my-clips` para regenerar URLs presignadas al responder estados/listados.
- Se incorporaron endpoints de videos autenticados: `GET /api/v1/videos/my-videos`, `GET /api/v1/videos/{video_id}`, `PATCH /api/v1/videos/{video_id}`, `DELETE /api/v1/videos/{video_id}` con ownership checks y serializacion unificada.
- Se agregaron endpoints de clips por `job_id`: `GET /api/v1/jobs/{job_id}` y `DELETE /api/v1/jobs/{job_id}`, incluyendo borrado de objeto en storage cuando corresponde.

## Commits realizados

- `fix(worker): stabilize processing flow and media output`
- `feat(jobs): add smart auto-clips and user clips listing`
- `feat(api): add search to my-clips and new my-videos endpoint`
- `feat(api): accept optional reframe filters in manual jobs`
- `feat(api): add authenticated video CRUD endpoints`
- `feat(api): add clip detail and delete endpoints for library actions`

## Archivos clave

- `backend/api/app/api/v1/endpoints/job.py`
- `backend/api/app/api/v1/endpoints/video.py`
- `backend/api/app/services/job_service.py`
- `backend/api/app/services/video_service.py`
- `backend/api/app/services/video_worker_service.py`
- `backend/worker/app/pipeline.py`
- `backend/worker/app/worker.py`
- `docs/backend-pr-log.md`

## Validaciones locales

Intentado en `backend/api/`:

- `pytest -q` -> No ejecutado (comando `pytest` no disponible en entorno local actual)

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Integracion de cambios backend/frontend de `feature/frontend-backend-timeline-library-flow`
- [x] Documentacion actualizada

## Objetivo de la rama

Registrar por separado los ajustes de backend detectados durante `feature/frontend-sync-upload-develop`, para enviarlos en PR backend independiente del PR frontend.

Rama de trabajo origen: `feature/frontend-sync-upload-develop`.

## Cambios implementados (backend)

- Se habilito en `backend/api/app/services/video_service.py` la aceptacion de `application/octet-stream` cuando la extension es valida (ej. `.webm`), evitando rechazo de uploads desde drag/drop en navegador.
- Se actualizo `backend/worker/app/pipeline.py` para usar `WORKER_OUTPUT_DIR` y default seguro `/tmp/worker`, reduciendo fallos por permisos en rutas temporales.

## Nota operativa para deploy

- Validar en cada entorno que `WORKER_OUTPUT_DIR` apunte a un path escribible por el proceso worker.
- Verificar permisos del volumen temporal en infraestructura para prevenir `PermissionError` durante normalizacion/procesamiento.

## Commits relacionados

- `fix(frontend): stabilize auto2 flow and unblock video uploads` (incluye estos cambios backend en el mismo commit)

## Archivos clave

- `backend/api/app/services/video_service.py`
- `backend/worker/app/pipeline.py`
- `docs/backend-pr-log.md`
