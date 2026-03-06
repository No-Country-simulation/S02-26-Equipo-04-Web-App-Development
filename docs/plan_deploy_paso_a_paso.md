# Plan de deploy paso a paso (backend)

Objetivo: desplegar backend de HaceloCorto en cloud con esta arquitectura:

- API y worker en Render
- PostgreSQL en Neon
- Redis en Upstash
- Storage S3-compatible en Cloudflare R2

Este plan esta pensado para staging/pruebas primero y luego produccion.

Estado actual (2026-03-05):

- Neon creado (`haceloCorto-backend`, region us-east-1).
- Upstash Redis creado (`haceloCorto-redis`, TLS habilitado).
- Cloudflare R2 creado (bucket `hacelocorto-videos`).
- Siguiente paso: terminar Render (API + worker) con esta rama.

## 0) Rama de trabajo

- Rama sugerida: `chore/deploy-render-upstash-r2`
- No desplegar desde `develop` directo hasta validar en staging.

## 1) Cuentas y recursos

### 1.1 Neon (PostgreSQL)

Crear proyecto:

- Nombre: `haceloCorto-backend`
- Region: `AWS us-east-1`

Guardar 2 URLs:

- `DATABASE_URL_POOLED` (pooling ON) -> para API/worker
- `DATABASE_URL_DIRECT` (pooling OFF) -> para migraciones Alembic

Notas:

- Las URLs deben incluir `sslmode=require`.
- Si una credencial se expone, hacer `Reset password` y regenerar URL.

### 1.2 Upstash (Redis)

Crear DB Redis:

- Nombre: `haceloCorto-redis`
- Region primaria: `us-east-1`
- Eviction: OFF (recomendado para no perder jobs)

Guardar:

- `REDIS_URL` (formato `rediss://default:<password>@<host>:6379`)
- Opcional: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`

Seguridad:

- Si token/password quedo expuesto, rotar credenciales antes del deploy.

### 1.3 Cloudflare R2 (S3-compatible)

Crear:

- Bucket: `videos` (o `hacelocorto-videos`)
- API token para R2
- Access Key ID + Secret Access Key

Guardar:

- `R2_ENDPOINT` (ej: `<account_id>.r2.cloudflarestorage.com`)
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`

Opcional recomendado:

- Dominio publico/CDN para entrega de videos.

## 2) Variables de entorno objetivo

Estas variables deben cargarse en Render para API y worker.

Nota:

- Para cloud, cargar en el panel de Render (no commitear secretos al repo).
- El archivo `.env` local sirve para pruebas en tu maquina.

### 2.1 Core

- `ENVIRONMENT=production`
- `DEBUG=false`
- `DATABASE_URL=<DATABASE_URL_POOLED>`
- `SECRET_KEY=<minimo 32 caracteres>`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=10080`

### 2.2 Redis

- `REDIS_URL=<rediss://...>`
- `REDIS_DB=0`

Compatibilidad:

- En cloud priorizar `REDIS_URL` (TLS).
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` quedan para entorno local/legacy.

### 2.3 Storage (R2 usando variables MinIO actuales)

- `MINIO_ENDPOINT=<R2_ENDPOINT>`
- `MINIO_ACCESS_KEY=<R2_ACCESS_KEY_ID>`
- `MINIO_SECRET_KEY=<R2_SECRET_ACCESS_KEY>`
- `MINIO_BUCKET_VIDEOS=<R2_BUCKET>`
- `MINIO_SECURE=true`
- `MINIO_PUBLIC_ENDPOINT=<dominio_publico_o_r2_endpoint>`
- `MINIO_PUBLIC_SECURE=true`

### 2.4 CORS y OAuth

- `ALLOWED_ORIGINS=<frontend_url_1,frontend_url_2>`
- `GOOGLE_CLIENT_ID=<si aplica>`
- `GOOGLE_CLIENT_SECRET=<si aplica>`
- `GOOGLE_REDIRECT_URI=<frontend_callback_url>`

## 3) Cambios minimos de codigo para Upstash TLS

Estado actual:

- El backend usa `REDIS_HOST/PORT/PASSWORD` sin TLS explicito.
- Upstash requiere TLS (`rediss://`).

Cambios minimos recomendados:

1. Agregar `REDIS_URL` opcional en `backend/api/app/core/config.py`.
2. En `backend/api/app/utils/redis_client.py`:
   - Si existe `REDIS_URL`, usar `redis.from_url(REDIS_URL, decode_responses=True)`.
   - Si no existe, mantener logica actual `host/port/password`.
3. En `backend/worker/app/worker.py` (`check_redis`):
   - Reusar cliente que soporte `REDIS_URL`.
4. En `backend/worker/Dockerfile` (healthcheck):
   - Validar Redis via `REDIS_URL` cuando exista.

Objetivo: compatibilidad dual local + cloud.

## 4) Render: servicios a crear

Antes de crear servicios en Render:

- Hacer commit y push de esta rama (`chore/deploy-render-upstash-r2`) para que Render pueda leer `render.yaml`.

Crear 2 servicios en Render desde el repo:

1. Web Service (API)
2. Background Worker (worker)

### 4.0 Opcion recomendada: Blueprint con `render.yaml`

Archivo versionado en repo: `render.yaml`.

Flujo recomendado:

1. En Render: `New` -> `Blueprint`.
2. Seleccionar el repo y rama `chore/deploy-render-upstash-r2`.
3. Render detecta `render.yaml` y propone `hacelocorto-api` + `hacelocorto-worker`.
4. Completar variables `sync: false` (secretos) directamente en panel.
5. Deploy.

Ventaja: infraestructura reproducible y facil de auditar por todo el equipo.

### 4.1 API service

- Root directory: `backend/api`
- Runtime: Docker
- Puerto: Render detecta automaticamente (app escucha en 8000)
- Healthcheck path: `/api/v1/health`
- Start command: definido en Dockerfile (`uvicorn` sin `--reload`, usando `${PORT:-8000}`)

### 4.2 Worker service

- Root directory: `backend`
- Runtime: Docker
- Dockerfile: `worker/Dockerfile`
- Sin puerto publico

## 5) Migraciones DB

Correr migraciones una vez por release:

- Usar `DATABASE_URL_DIRECT` para el job de migracion (conexion directa de Neon, sin pooler).
- Comando esperado: `alembic upgrade head` (en entorno API).

Sugerencia practica en Render:

- Abrir `Shell` del servicio API.
- Ejecutar temporalmente:
  - `export DATABASE_URL="<DATABASE_URL_DIRECT>"`
  - `alembic upgrade head`
- Cerrar shell (el servicio sigue con `DATABASE_URL` pooled para runtime normal).

Verificar:

- Tablas creadas correctamente.
- Sin errores de permisos/SSL contra Neon.

## 6) Checklist de validacion post-deploy

### 6.0 Infra/Config

- Rama deploy pusheada y seleccionada en Render.
- API y worker en estado `Live`.
- Todas las variables obligatorias cargadas (sin usar `.env` en cloud).

### 6.1 API

- `GET /api/v1/health` responde 200
- Logs sin errores de DB
- Logs sin errores de Redis

### 6.2 Worker

- Worker inicia sin crash
- Conecta a Redis
- Consume cola correctamente

### 6.3 Storage

- Upload de video exitoso
- URL presignada valida
- Descarga desde frontend sin error CORS

### 6.4 Flujo funcional

- Crear job desde API
- Worker procesa job
- Estado de job pasa a DONE/FAILED correctamente
- Video final disponible en storage

## 7) Troubleshooting rapido

- Error Redis TLS: revisar `REDIS_URL` y soporte `rediss://` en codigo.
- Error DB SSL: confirmar `sslmode=require` en Neon URL.
- Error bucket: validar `MINIO_*` contra endpoint R2.
- Error CORS: revisar `ALLOWED_ORIGINS` exactos (sin slash final).
- Worker lento/caido: subir plan de Render (RAM/CPU) para Whisper/FFmpeg.

## 8) Pendientes para produccion

- Configurar dominio propio para API
- Configurar observabilidad (logs/alertas)
- Rotacion periodica de secretos
- Backup/retention de DB y bucket
- Definir politica de escalado para worker

---

Documento vivo: actualizar este archivo en cada ajuste de infraestructura.
