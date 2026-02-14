# Backend PR Worklog

## Objetivo de la rama

Corregir CORS en backend para habilitar login y registro desde frontend en desarrollo local y dejar guia clara para origenes de produccion.

Rama de trabajo: `feature/backend-cors-local-origins`.

## Cambios realizados

- Se ampliaron los origenes permitidos por defecto en `backend/api/app/core/config.py` para incluir `localhost` y `127.0.0.1` en puertos `3000` y `5173`.
- Se mantuvo el uso de `settings.ALLOWED_ORIGINS` en `CORSMiddleware`, evitando valores hardcodeados en `main.py`.
- Se actualizo `backend/api/.env.example` con una lista CORS local completa y placeholder para dominio frontend en Railway.
- Se valido preflight CORS con `OPTIONS /api/v1/auth/login` para `http://localhost:3000` y `http://127.0.0.1:3000`.

## Commits realizados

- `fix(cors): permitir origins locales de frontend`
- `docs(backend): agregar bitacora PR y ejemplo CORS Railway`

## Archivos clave

- `backend/api/app/core/config.py`
- `backend/api/.env.example`
- `docs/backend_pr_log.md`

## Validaciones locales

Ejecutado en `backend/`:

- `docker compose up -d api` -> OK
- `curl -i -X OPTIONS "http://localhost:8000/api/v1/auth/login" -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST"` -> OK (`access-control-allow-origin` presente)
- `curl -i -X OPTIONS "http://localhost:8000/api/v1/auth/login" -H "Origin: http://127.0.0.1:3000" -H "Access-Control-Request-Method: POST"` -> OK (`access-control-allow-origin` presente)

## Nota para deploy (Railway)

- En produccion, `ALLOWED_ORIGINS` debe incluir el dominio del frontend (no el dominio del backend/docs).
- Ejemplo: `https://tu-frontend-production.up.railway.app`.
