# Backend PR Log

## Branch
- `fix/jobs-endpoints-debug`

## Objetivo
- Restaurar y estabilizar autenticacion OAuth.
- Diagnosticar endpoints de jobs.
- Asegurar que el worker produzca salida final recortada (sin overlay de debug).
- Agregar generacion automatica de clips shorts desde un video fuente.

## Cambios aplicados

### 1) OAuth y autenticacion
- `api/app/core/dependencies.py`
  - `get_current_user` ahora admite `sub` como UUID y como email (fallback).
  - Evita rechazos de token cuando el `sub` no coincide con un formato unico.
- `api/app/services/google_oauth_service.py`
  - JWT emitido con `subject=str(user.id)` para alinear con el login tradicional.

### 2) Configuracion para arranque del worker
- `api/app/core/config.py`
  - `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` pasan a tener default vacio.
  - Evita que el worker falle al iniciar por credenciales OAuth faltantes cuando no son necesarias para jobs.

### 3) Endpoints/jobs y robustez del worker
- `worker/app/worker.py`
  - Se agregaron `continue` en rutas de error para cortar el flujo correctamente.
  - Evita errores encadenados cuando falla el pipeline (variables no definidas en pasos siguientes).

### 4) Pipeline de video (reframe/crop)
- `worker/app/pipeline.py`
  - `DEBUG` ahora se controla por variable de entorno `WORKER_PIPELINE_DEBUG` (default `false`).
  - Se corrige inicializacion de `CameraDirector`: se pasa `FINAL_W` (ancho de recorte) en lugar de `FINAL_H`.
  - Se fuerza `crop_w` par para compatibilidad con encoder H.264.
  - En videos ya normalizados, el segmento se re-encodea (en vez de `copy`) para evitar cortes inestables sin stream de video.
  - Se estandariza salida a `.mp4` para `normalized_`, `processed_` y `result_` (evita errores de muxer WebM con `libx264/aac`).
  - Se agrega fallback cuando no hay stream de audio: exporta video-only en vez de fallar.
  - Fix de audio en normalizacion con scale: ahora preserva/inyecta audio usando `input_stream.audio` al re-encodear.
  - Resultado esperado: salida final recortada vertical (9:16) sin overlays cuando debug esta apagado.

### 5) Docker Compose
- `docker-compose.yml`
  - Se agrega en `worker.environment`: `WORKER_PIPELINE_DEBUG=false`.

### 6) Worker upload naming
- `worker/app/worker.py`
  - El upload a MinIO usa el nombre real del archivo generado por pipeline (`os.path.basename(video_local_path)`).
  - Evita inconsistencias de extension cuando el input original es `.webm` y el output final es `.mp4`.

### 7) Endpoint auto-clips
- `api/app/schemas/job.py`
  - Se agregan schemas para auto clips:
    - `JobAutoReframeRequest`
    - `JobAutoReframeItem`
    - `JobAutoReframeResponse`
- `api/app/services/job_service.py`
  - Se refactoriza creacion de jobs con helper interno reutilizable.
  - Nuevo metodo `auto_reframe_video(...)` para generar multiples jobs en lote.
  - Estrategia de segmentos v2:
    - deteccion de tramos no silenciosos con `ffmpeg silencedetect` sobre URL temporal del video,
    - ranking de highlights por duracion,
    - seleccion de clips con separacion minima para evitar solapamientos,
    - fallback a distribucion temporal uniforme si no hay señal util.
  - Si la duracion no esta en DB, se obtiene con `ffprobe` (usando URL temporal MinIO).
- `api/app/api/v1/endpoints/job.py`
  - Nuevo endpoint `POST /api/v1/jobs/reframe/{video_id}/auto`.
  - Permite pedir 1..20 clips con duracion configurable (5..120s).
  - Nuevo endpoint `GET /api/v1/jobs/my-clips` con paginado (`limit`, `offset`) para listar clips generados del usuario.

- `api/app/schemas/job.py`
  - Nuevos schemas para listados de clips del usuario:
    - `UserClipItem`
    - `UserClipsResponse`

### 8) API runtime para analisis de highlights
- `api/Dockerfile`
  - Se instala `ffmpeg` para habilitar `ffprobe` + `silencedetect` en API.

## Validaciones ejecutadas
- Salud API:
  - `GET /api/v1/health` -> `healthy`.
- Endpoints jobs (smoke tests):
  - `POST /api/v1/jobs/reframe/{video_id}` -> `201`.
  - `POST /api/v1/jobs/reframe/{video_id}/auto` -> `201` (crea multiples jobs).
  - `GET /api/v1/jobs/status/{job_id}` -> `200`.
  - Parametros invalidos -> `400`.
  - Job de otro usuario -> `404`.
  - Video inexistente -> `404`.
- Worker:
  - Arranque correcto y escucha de cola confirmado por logs.
  - `docker exec worker python -c "from worker.app.pipeline import DEBUG; print(DEBUG)"` -> `False`.
  - Prueba directa del pipeline dentro de contenedor devuelve path de salida: `tmp/result/result_reframe_valid_input.mp4`.
  - `ffprobe` sobre salida final: `h264`, `404x720` (formato vertical).
  - Flujo completo por endpoint con video valido: job finaliza `DONE` con `output_path`.
- Flujo completo con video `.webm` real (`/home/guillenec/Vídeos/Videomatch - José María Listorti Bailando Chayanne (HD) [hg2G__cvrz0].webm`) finaliza `DONE` y genera output `.mp4`.
- Flujo auto clips probado con 3 segmentos (`clips_count=3`, `clip_duration_sec=7`) y los 3 jobs completados en `DONE`.
- Flujo auto clips v2 probado con 5 segmentos (`clips_count=5`, `clip_duration_sec=8`):
  - respuesta incluye `used_video_duration_sec=131`,
  - clips generados en offsets distintos (ej: `2-10`, `24-32`, `41-49`, `82-90`, `117-125`).
- Validacion de audio en clip generado:
  - job finaliza `DONE` y `ffprobe` sobre `output_path` devuelve stream de audio `aac`.
- Validacion endpoint de listado:
  - `GET /api/v1/jobs/my-clips?limit=5&offset=0` devuelve clips del usuario autenticado.

## Evidencia funcional
- Se verifico al menos un job en estado `DONE` con `output_path` presente en DB.
- Los jobs con input invalido quedan en `FAILED` sin cascada de errores secundarios.
- Se verifico salida vertical sin overlay de debug al procesar un video valido.

## Pendientes recomendados
- Correr reframe con video real y validar visualmente:
  - seguimiento de rostro,
  - recorte vertical final,
  - ausencia de overlays en output.
- Ajustar threshold/logica de seguimiento si en ciertos clips el encuadre no acompana como se espera.
