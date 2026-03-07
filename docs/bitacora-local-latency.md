# Bitacora de optimizacion local (clips)

## Fecha
- 2026-03-07

## Problema reportado
- En entorno local, la generacion de clips tardaba demasiado y los resultados demoraban en aparecer en frontend.

## Diagnostico
- El worker estaba forzando subtitulos en auto-reframe aunque el usuario no los pidiera.
- Los jobs hijos de auto-reframe se publicaban dos veces en Redis.
- Whisper se cargaba en cada generacion de subtitulos (costo alto por job).
- Habia llamadas redundantes para generar URLs publicas de MinIO solo para logging.
- El frontend hacia polling muy agresivo y duplicado (estado jobs + hidratacion de biblioteca en paralelo).
- El logging de librerias externas era ruidoso en local y agregaba overhead.

## Cambios aplicados

### Backend
- `backend/api/app/services/queue_service.py`
  - `publish_auto_reframe_job` ahora incluye `subtitles` en payload.
- `backend/api/app/services/job_service.py`
  - Se propaga `subtitles` al publicar jobs AUTO_REFRAME.
  - Correccion de tipo en `auto_reframe_video2(..., subtitles: bool | None)`.
- `backend/worker/app/worker.py`
  - AUTO_REFRAME usa `subtitles` real del payload.
  - Se elimino doble publish de jobs hijos.
  - Se eliminaron URLs publicas de MinIO usadas solo para logs.
- `backend/worker/app/pipeline.py`
  - Se agrego cache lazy del modelo Whisper (singleton por proceso worker).
- `backend/api/app/core/logging.py`
  - Se bajo a `WARNING` el nivel de logs de `botocore`, `boto3`, `urllib3`, `multipart`, `httpx`, `httpcore`.
- `backend/docker-compose.yml`
  - `api`: `DEBUG=False`, `LOG_LEVEL=INFO`.
  - `worker`: `LOG_LEVEL=INFO`.

### Frontend
- `frontend/src/app/app/page.tsx`
  - Se muestran placeholders de clips pendientes cuando ya existe `autoJobCount`.
  - Polling de estado optimizado: solo consulta jobs no terminales o sin `outputPath`.
  - Intervalo de polling de estado ajustado a 7s.
  - Hidratacion de biblioteca mas conservadora (sin competir con polling activo).
  - Intervalo de hidratacion ajustado a 12s y menor numero de intentos.

## Resultado esperado
- Menor tiempo de CPU por job cuando subtitulos estan desactivados.
- Menor carga de cola (sin duplicados).
- Menor latencia cuando subtitulos estan activos por cache de Whisper.
- Menor ruido de logs y menor overhead de I/O.
- UI mas estable: muestra progreso desde el inicio y evita consultas redundantes.

## Verificacion sugerida
- Subir un video corto desde Home y medir:
  - tiempo hasta estado `DONE`;
  - tiempo hasta ver preview en tarjeta.
- Repetir con subtitulos ON y OFF para comparar.
- Confirmar en Redis (`LLEN reframe_queue`) que no haya duplicacion anomala.
