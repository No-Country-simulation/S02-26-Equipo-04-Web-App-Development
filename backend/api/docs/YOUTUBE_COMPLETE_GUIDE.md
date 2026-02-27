# Guia Completa: YouTube OAuth + Publicacion de Clips

Guia paso a paso para probar la integracion completa de YouTube desde Swagger UI.

---

## Tabla de Contenidos

1. [Configuracion Inicial](#1-configuracion-inicial)
2. [Preparar Ambiente Docker](#2-preparar-ambiente-docker)
3. [Flujo Completo en Swagger](#3-flujo-completo-en-swagger)
4. [Troubleshooting](#4-troubleshooting)
5. [Referencia Tecnica](#5-referencia-tecnica)

---

## 1. Configuracion Inicial

### Prerequisitos

#### A. Google Cloud Console
1. Proyecto creado con las APIs habilitadas:
   - YouTube Data API v3
   - Google+ API
2. Credenciales OAuth 2.0 configuradas:
   - Client ID y Client Secret generados
   - Redirect URI: `http://localhost:3000/auth/callback`
3. Publishing Status: `Testing`
4. Tu email en la lista de Test Users

#### B. Variables de Entorno
Verificar que `backend/api/.env` tenga:
```bash
GOOGLE_CLIENT_ID=<TU_CLIENT_ID>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<TU_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

#### C. Sistema Local
- Docker Desktop corriendo
- Al menos 4GB RAM disponible
- Un video `.mp4` de prueba (corto, menos de 30 segundos)

---

## 2. Preparar Ambiente Docker

### Opcion A: Primera vez (ambiente limpio)

```powershell
cd backend

# Levantar todos los servicios
docker-compose up -d --build

# Esperar 10 segundos a que arranque PostgreSQL
Start-Sleep -Seconds 10

# Aplicar migraciones de base de datos
docker exec fastapi alembic upgrade head

# Verificar que todo este corriendo
docker-compose ps
```

### Opcion B: Si ya tenes Docker corriendo

```powershell
cd backend
docker-compose up -d --build
docker exec fastapi alembic upgrade head
```

Verificar en los logs que no haya errores:
```powershell
docker logs fastapi --tail 20
```

Resultado esperado: la linea `Application startup complete` sin errores.

---

## 3. Flujo Completo en Swagger

Abrir Swagger UI en: **http://localhost:8000/docs**

---

### PASO 1: Health Check

Verificar que el API funciona.

1. Expandir: **GET /health**
2. Click: **Try it out** > **Execute**
3. Respuesta esperada: `{"status": "healthy"}`

---

### PASO 2: Obtener URL de Autorizacion de Google

1. Expandir: **GET /api/v1/auth/google/authorize**
2. Click: **Try it out** > **Execute**
3. Respuesta esperada:
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=...",
  "state": "cpEqW9MkYXBjPjEIyBUuin3PvK0iFhj40A4jYj38LqY"
}
```
4. **Copiar la URL completa** (desde `https://` hasta el final)
5. **Copiar el valor de `state`** (se necesita en el paso 4)

---

### PASO 3: Autorizar con Google (Navegador)

IMPORTANTE: Hacer esto rapido, el code expira en 10 minutos.

1. Pegar la URL copiada en una nueva pestaña del navegador
2. Iniciar sesion con tu cuenta de Google (la que esta como Test User)
3. Aceptar los permisos solicitados (YouTube upload, etc.)
4. Seras redirigido a `http://localhost:3000/auth/callback?code=...&state=...`
   - La pagina puede mostrar error, es normal.
5. **Copiar el parametro `code`** de la URL (el texto entre `code=` y `&scope`)

---

### PASO 4: Intercambiar Code por JWT Token

1. Volver a Swagger UI
2. Expandir: **POST /api/v1/auth/google/callback**
3. Click: **Try it out**
4. Completar el request body:
```json
{
  "code": "PEGAR_AQUI_EL_CODE_DEL_PASO_3",
  "state": "PEGAR_AQUI_EL_STATE_DEL_PASO_2"
}
```
5. Click: **Execute**
6. Respuesta esperada:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```
7. **Copiar el `access_token` completo** (empieza con `eyJ`)

Este token dura 7 dias.

---

### PASO 5: Autorizar Swagger UI con el JWT Token

1. En la parte superior derecha de Swagger UI, buscar el boton **Authorize** (icono de candado)
2. Click en **Authorize**
3. En el campo **username**, pegar el token completo (`eyJ...`)
4. En el campo **password**, escribir cualquier cosa (por ejemplo: `x`)
5. Click en **Authorize** > **Close**

A partir de ahora, todos los endpoints protegidos usaran este token automaticamente.

---

### PASO 6: Verificar Conexion con YouTube

1. Expandir: **GET /api/v1/youtube/status**
2. Click: **Try it out** > **Execute**
3. Respuesta esperada:
```json
{
  "connected": true,
  "provider_username": null,
  "provider_user_id": "113822179860751389711",
  "token_expires_at": "2026-02-27T15:19:37.874339",
  "is_expired": false
}
```

Validar que:
- `connected` sea `true`
- `is_expired` sea `false`

Si `connected` es `false`, repetir los pasos 2 al 5.

---

### PASO 7: Subir un Video

1. Expandir: **POST /api/v1/videos/upload**
2. Click: **Try it out**
3. Seleccionar un archivo `.mp4` de prueba (corto, menos de 30 seg)
4. Click: **Execute**
5. **Copiar el `video_id`** de la respuesta

---

### PASO 8: Procesar el Video (Reframe)

1. Expandir: **POST /api/v1/jobs/reframe/{video_id}**
2. Pegar el `video_id` del paso anterior
3. Request body:
```json
{
  "start_sec": 0,
  "end_sec": 5,
  "job_type": "REFRAME",
  "watermark": "Hacelo Corto"
}
```
4. Click: **Execute**
5. **Copiar el `job_id`** de la respuesta

---

### PASO 9: Esperar a que Termine el Procesamiento

1. Expandir: **GET /api/v1/jobs/status/{job_id}**
2. Pegar el `job_id`
3. Click: **Execute**
4. Repetir hasta que el campo `status` sea `"DONE"`

---

### PASO 10: Publicar el Clip en YouTube

1. Expandir: **POST /api/v1/youtube/publish/{job_id}**
2. Pegar el `job_id` (el mismo del paso 8)
3. Request body:
```json
{
  "title": "Mi primer clip con Hacelo Corto",
  "description": "Video procesado con Hacelo Corto",
  "privacy": "private"
}
```

Opciones de `privacy`:
- `"private"` - Solo vos lo ves (recomendado para testing)
- `"unlisted"` - Cualquiera con el link lo ve
- `"public"` - Aparece en busquedas y en tu canal

4. Click: **Execute**
5. Respuesta esperada:
```json
{
  "success": true,
  "message": "Video publicado en YouTube exitosamente",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_video_id": "dQw4w9WgXcQ",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Mi primer clip con Hacelo Corto",
  "privacy": "private",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg"
}
```

6. Abrir el `youtube_url` en el navegador para verificar que el video esta en YouTube.

---

## 4. Troubleshooting

### Error: `relation "oauth_tokens" does not exist`

Causa: Las migraciones de base de datos no se aplicaron.

Solucion:
```powershell
docker exec fastapi alembic upgrade head
```

Si falla porque hay migraciones inconsistentes, limpiar la base:
```powershell
docker stop fastapi worker
docker exec postgres psql -U postgres -c "DROP DATABASE fastapi_db;"
docker exec postgres psql -U postgres -c "CREATE DATABASE fastapi_db;"
docker start fastapi worker
Start-Sleep -Seconds 3
docker exec fastapi alembic upgrade head
```

---

### Error: `403 You do not have access to this page` (Google)

Causa: Tu cuenta no esta en la lista de Test Users.

Solucion:
1. Ir a: https://console.cloud.google.com/apis/credentials/consent
2. Verificar que Publishing status sea `Testing`
3. En "Test users", agregar tu email
4. Esperar 5 minutos y reintentar

---

### Error: `400 Invalid grant: code expired`

Causa: El authorization code expiro (dura solo 10 minutos).

Solucion: Volver al Paso 2 y obtener un nuevo code.

---

### Error: `401 Unauthorized` en endpoints protegidos

Causa: No se autorizo Swagger UI con el token.

Solucion: Repetir el Paso 5 (boton Authorize, pegar token en username).

---

### Error: `El clip aun no esta listo. Estado actual: PENDING`

Causa: El job todavia no termino de procesarse.

Solucion: Esperar. Repetir el Paso 9 hasta que `status` sea `DONE`.

---

### Error: `Cuota de YouTube API excedida`

Causa: Se excedio el limite diario de YouTube API (6 uploads por dia aprox).

Solucion: Esperar 24 horas (la quota se resetea a medianoche PST).

---

## 5. Referencia Tecnica

### Endpoints Disponibles

| Metodo | Endpoint | Descripcion | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/auth/google/authorize` | Obtener URL de autorizacion | No |
| POST | `/api/v1/auth/google/callback` | Intercambiar code por JWT | No |
| GET | `/api/v1/youtube/status` | Verificar conexion YouTube | JWT |
| POST | `/api/v1/youtube/publish/{job_id}` | Publicar clip en YouTube | JWT |
| POST | `/api/v1/videos/upload` | Subir video | JWT |
| POST | `/api/v1/jobs/reframe/{video_id}` | Crear job de reframe | JWT |
| GET | `/api/v1/jobs/status/{job_id}` | Consultar estado del job | JWT |

### Renovacion Automatica de Tokens

- El access token de YouTube dura aprox. 1 hora.
- El refresh token es permanente.
- El sistema renueva el access token automaticamente cuando expira.
- No hace falta hacer nada manual.

### Limites de YouTube API

Cuota diaria: 10,000 unidades por dia.

| Operacion | Costo |
|-----------|-------|
| Upload de video | 1,600 unidades |
| List videos | 1 unidad |
| Update video | 50 unidades |

Resultado: se pueden subir aprox. 6 videos por dia con la cuota gratuita.

---

**Ultima actualizacion**: Febrero 27, 2026
**Version**: 2.0.0
**Equipo**: Hacelo Corto - Backend
