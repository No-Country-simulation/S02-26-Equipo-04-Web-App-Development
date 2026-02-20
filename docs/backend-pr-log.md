# Backend PR Worklog

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
