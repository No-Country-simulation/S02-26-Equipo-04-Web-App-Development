# Frontend + Backend PR Worklog

## Objetivo de la rama

Integrar sobre `develop` actualizado el flujo completo de timeline + biblioteca en frontend y backend, dejando operativo el circuito upload -> procesamiento -> biblioteca -> edicion -> compartir.

Rama de trabajo: `feature/integracion-timeline-library-flow`.

## Cambios realizados

- Se sincronizo la base de trabajo con `develop` remoto y se recreo una rama limpia para integrar sin arrastrar archivos temporales locales.
- Se integraron cambios de backend para worker estable, jobs automaticos/manuales, listado de clips, filtros de reframe y regeneracion de URLs presignadas.
- Se agregaron endpoints y servicios para CRUD autenticado de videos (`my-videos`, detalle, rename, delete) y acciones de biblioteca de clips (detalle y delete por `job_id`).
- Se integraron cambios de frontend en Home, Timeline y Library con polling estable, persistencia de draft, paginacion, busqueda backend y acciones CRUD.
- Se incorporo la ruta `frontend/src/app/app/share/[clipId]/page.tsx` y se reforzo el deep-link de edicion desde biblioteca a timeline.
- Se aplico ajuste visual del dashboard (paleta Catppuccin) y correccion del comportamiento del logo en navegacion.
- Se resolvieron conflictos de integracion entre avances de `develop` y `feature/frontend-backend-timeline-library-flow` en archivos de auth/video.
- Se actualizaron logs de trabajo existentes en `docs/frontend-pr-log.md` y `docs/backend-pr-log.md` con las nuevas entradas de esta rama.

## Commits realizados

- `fix(worker): stabilize processing flow and media output`
- `feat(jobs): add smart auto-clips and user clips listing`
- `feat(frontend): wire home upload flow to auto reframe jobs endpoint`
- `feat(frontend): move preview workflow to timeline and fetch user clips`
- `fix(api): regenerate clip output urls for status and my-clips`
- `fix(frontend): handle unsupported video play promise in timeline`
- `fix(frontend): persist home clip draft and stabilize preview polling`
- `feat(frontend): add pagination to timeline and library clips`
- `fix(frontend): improve home results loading and live preview transitions`
- `feat(api): add search to my-clips and new my-videos endpoint`
- `feat(frontend): add backend search and original videos library view`
- `feat(api): accept optional reframe filters in manual jobs`
- `feat(frontend): wire timeline editor to manual reframe endpoint`
- `feat(api): add authenticated video CRUD endpoints`
- `feat(frontend): add rename and delete actions to library videos`
- `feat(api): add clip detail and delete endpoints for library actions`
- `feat(frontend): add clip share route and stronger timeline edit deep-link`
- `style(frontend): switch dashboard palette to catppuccin and fix home logo link`
- `docs(worklog): registrar integracion timeline-library en rama nueva`

## Archivos clave

- `backend/api/app/api/v1/endpoints/job.py`
- `backend/api/app/api/v1/endpoints/video.py`
- `backend/api/app/services/job_service.py`
- `backend/api/app/services/video_service.py`
- `backend/worker/app/pipeline.py`
- `backend/worker/app/worker.py`
- `frontend/src/app/app/page.tsx`
- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/app/app/library/page.tsx`
- `frontend/src/app/app/share/[clipId]/page.tsx`
- `frontend/src/services/videoApi.ts`
- `docs/frontend-pr-log.md`
- `docs/backend-pr-log.md`
- `docs/front_back-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

Ejecutado en `backend/`:

- `docker compose up -d --build` -> OK
- `docker compose ps` -> servicios arriba
- `worker` saludable y escuchando jobs
- `alembic upgrade heads` requerido por multiple heads para crear esquema completo

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Integracion completa de `feature/frontend-backend-timeline-library-flow`
- [x] Documentacion frontend/backend actualizada
- [x] Log unificado frontend+backend agregado

## Actualizacion de la rama (speaker split)

### Objetivo

Agregar una opcion de salida para generar clips en formato "speaker split": arriba enfoque al hablante (seguimiento facial) y abajo plano general horizontal completo.

### Cambios realizados

- Se agrego `output_style` en payloads de jobs manuales y automaticos para backend (`vertical` | `speaker_split`).
- Se propago `output_style` desde API -> service -> cola Redis -> worker.
- Se extendio el pipeline del worker para soportar composicion `speaker_split` apilando foco vertical en la parte superior y vista general letterbox en la inferior.
- Se agrego selector de estilo en Home (`frontend/src/app/app/page.tsx`) antes del upload para elegir entre `Vertical clasico 9:16` y `Split speaker`.
- Se actualizo `frontend/src/services/videoApi.ts` para enviar `output_style` al crear jobs automaticos.

### Archivos clave

- `backend/api/app/schemas/job.py`
- `backend/api/app/api/v1/endpoints/job.py`
- `backend/api/app/services/job_service.py`
- `backend/api/app/services/queue_service.py`
- `backend/worker/app/worker.py`
- `backend/worker/app/pipeline.py`
- `frontend/src/app/app/page.tsx`
- `frontend/src/services/videoApi.ts`

### Validaciones locales

- `npm run lint` en `frontend/` -> OK
- `python3 -m py_compile` sobre archivos backend modificados -> OK

## Ajuste de calidad visual (speaker split)

### Problema detectado

- En clips `speaker_split`, el panel superior podia deformar la imagen (aspecto estirado/achatado).
- En entrevistas, algunos rostros quedaban demasiado al borde por recorte superior demasiado angosto.

### Correccion aplicada

- Se ajusto la composicion de `speaker_split` en `backend/worker/app/pipeline.py` para:
  - calcular el recorte superior con el **mismo aspect ratio** del panel destino (evita deformacion),
  - aumentar el espacio del panel superior para mostrar mejor el rostro,
  - mantener el panel inferior con plano general en letterbox sin distorsion.

## Ajuste de perfiles de contenido (entrevista/deportes)

### Objetivo

Evitar zoom excesivo en clips de futbol/deportes dentro de `speaker_split`, manteniendo mas contexto de jugada (jugador + balon + entorno).

### Cambios realizados

- Se agrego `content_profile` en requests de jobs (`interview` | `sports`) para reframe manual y automatico.
- Se propago `content_profile` en toda la cadena API -> service -> Redis -> worker -> pipeline.
- En Home se agrego selector de perfil de contenido al elegir `speaker_split`:
  - `Entrevista (mas foco en rostro)`
  - `Deportes (menos zoom, mas contexto)`
- En pipeline, `speaker_split` ahora adapta composicion por perfil:
  - `interview`: panel superior mas dominante y tracking mas directo.
  - `sports`: panel superior mas bajo y centro suavizado hacia el medio del frame para reducir paneo agresivo y zoom percibido.

### Archivos clave

- `backend/api/app/schemas/job.py`
- `backend/api/app/api/v1/endpoints/job.py`
- `backend/api/app/services/job_service.py`
- `backend/api/app/services/queue_service.py`
- `backend/worker/app/worker.py`
- `backend/worker/app/pipeline.py`
- `frontend/src/services/videoApi.ts`
- `frontend/src/app/app/page.tsx`

## Hotfix de persistencia de clips

### Problema detectado

- Los jobs terminaban el procesamiento en worker, pero fallaban al guardar resultado con error DB:
  `value too long for type character varying(500)` en `jobs.output_path`.
- Consecuencia: el clip no quedaba en `DONE` ni visible en Home/Biblioteca, aunque el archivo se subia a MinIO.

### Correccion aplicada

- En `backend/worker/app/worker.py` se dejo de persistir la URL firmada completa en `output_path`.
- Ahora se guarda el `storage_path` corto (ej. `s3://...`) y la API genera URL presignada al consultar estado/listados.
- Se ajusto manejo de errores en update de DB para hacer `rollback()` antes de marcar `FAILED`, evitando `PendingRollbackError` en cadena.

## Hotfix de estabilidad worker + Home

### Problemas detectados

- Algunos jobs terminaban procesamiento, pero el worker podia caer con `StaleDataError`/`ObjectDeletedError` al persistir estado final.
- En Home, en ciertos flujos quedaba UI desincronizada (skeleton sin clips hasta recargar/navegar).

### Correcciones aplicadas

- `backend/worker/app/worker.py`:
  - Se agrego persistencia de estado robusta con update directo por `job_id` (`update_job_state`) para evitar caidas por filas ausentes o stale ORM.
  - En fallos de pipeline/upload/update se guarda estado `FAILED` de forma tolerante a errores, sin tumbar el proceso principal.
- `frontend/src/app/app/page.tsx`:
  - Se agrego hydrate de respaldo desde `my-clips` cuando Home pierde estado local de jobs, para mostrar resultados sin requerir recarga manual.
- `backend/worker/app/pipeline.py`:
  - En perfil `sports`, el panel inferior de `speaker_split` usa `cover` (menos bandas negras) y ajuste de proporcion para reducir hueco visual.

## Hotfix timeline editor

### Problema detectado

- En timeline manual, la creacion de job podia reusar un job existente del mismo video (pendiente/running/failed), haciendo que el recorte solicitado no se encolara como nuevo trabajo.

### Correccion aplicada

- En `backend/api/app/services/job_service.py`, el flujo `reframe_video` paso a crear job nuevo (`allow_reuse=False`) para respetar cada solicitud del timeline editor.

## Mejora de autodeteccion de clips en Home

### Objetivo

Generar clips automaticos con deteccion real de momentos importantes y duracion variable definida por backend (sin hardcode fijo de 15s) para el flujo de Home/Panel.

### Cambios aplicados

- `backend/api/app/schemas/job.py`
  - `clips_count` y `clip_duration_sec` pasaron a opcionales en auto reframe.
  - Se amplio `content_profile` a `auto | interview | sports | music`.
- `backend/api/app/services/job_service.py`
  - Nuevo modo inteligente de seleccion de segmentos:
    - analisis de no-silencios (`silencedetect`),
    - deteccion de cambios de escena (`select='gt(scene,0.35)' + showinfo`),
    - ranking de candidatos con separacion minima.
  - Backend decide cantidad de clips si no viene en request (`2-5` segun duracion total).
  - Duracion por clip variable por perfil:
    - `sports`: mas corta y dinamica,
    - `music`: mas extensa para frase/coro,
    - `interview`: intermedia para idea completa.
  - En `content_profile=auto`, se resuelve perfil final por heuristica (nombre de archivo + densidad de escena + ratio de no-silencio).
  - Los jobs auto encolan el `resolved_profile` para que el worker aplique framing acorde.
- `frontend/src/services/videoApi.ts`
  - En auto reframe ya no envia defaults hardcodeados de `clips_count` y `clip_duration_sec`.
  - `content_profile` ahora soporta `auto` y `music`.
- `frontend/src/app/app/page.tsx`
  - Home ahora usa por defecto `Auto detectar` para perfil de contenido.
  - Se agrego opcion manual de override (`Entrevista`, `Deportes`, `Musica`) para pruebas.

### Validaciones

- `python3 -m py_compile` en backend -> OK
- `npm run lint` en frontend -> OK
- `docker compose up -d --build api worker` -> OK

## Ajuste fino de highlights para futbol/deportes

### Objetivo

Priorizar mejor la secuencia previa y posterior a jugadas importantes (pre-gol + gol + reaccion), no solo el instante del pico.

### Cambios aplicados

- En `backend/api/app/services/job_service.py` se incorporo ventana contextual para `sports`:
  - los anchors de highlights/escenas ahora se expanden de forma asimetrica,
  - mayor peso al contexto previo (~62%) y cierre posterior,
  - minima longitud garantizada por clip.
- Se reemplazo almacenamiento de duracion por almacenamiento de rango candidato (`start/end`) para mantener contexto exacto en deportes.

## Optimizacion de metadata de video (API liviana)

### Objetivo

Reducir carga del nodo `/api` durante upload, evitando extraccion pesada de metadata con `ffprobe` en tiempo de request y aprovechando metadata basica obtenida por frontend al seleccionar el archivo.

### Cambios aplicados

- `frontend/src/app/app/page.tsx`
  - Se agrego extraccion local de metadata del archivo antes de subir (`durationSeconds`, `width`, `height`) usando `HTMLVideoElement` + `onloadedmetadata`.
  - Se agrego fallback por timeout/error para no bloquear el upload si el navegador no puede leer metadata.
- `frontend/src/services/videoApi.ts`
  - `videoApi.upload(...)` ahora admite `clientMetadata` opcional y la envia como campos `multipart/form-data` (`duration_seconds`, `width`, `height`, `fps`).
- `backend/api/app/api/v1/endpoints/video.py`
  - El endpoint `POST /api/v1/videos/upload` acepta campos de metadata opcionales en `Form` junto al archivo.
  - Se normalizan valores numericos (`duration_seconds`, `fps`) a enteros seguros antes de persistir.
- `backend/api/app/services/video_service.py`
  - Se elimino el flujo de `ffprobe` durante upload en API.
  - Se agrega persistencia de metadata inicial enviada por cliente (`duration_seconds`, `width`, `height`, `fps`) sin procesamiento multimedia pesado.
- `backend/api/app/schemas/video.py`
  - Nuevo schema `ClientVideoMetadata` para validar metadata inicial opcional.

### Impacto esperado

- Menor latencia en `POST /videos/upload`.
- Menor bloqueo de recursos en `/api` por I/O/CPU de multimedia.
- Mejor separacion de responsabilidades: frontend aporta metadata para UX inicial y el procesamiento canonico queda preparado para worker/job flow.

### Validaciones

- `npm run lint` en `frontend/` -> OK
- `python3 -m py_compile` sobre archivos backend modificados -> OK
