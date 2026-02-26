# 🎬 Guía Completa: YouTube OAuth + Video Upload

**Guía definitiva para probar la integración completa de YouTube desde Swagger UI**

---

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#1-configuración-inicial)
2. [Preparar Ambiente Docker](#2-preparar-ambiente-docker)
3. [Probar OAuth Flow (Swagger UI)](#3-probar-oauth-flow-swagger-ui)
4. [Verificar Conexión YouTube](#4-verificar-conexión-youtube)
5. [Subir Video a YouTube](#5-subir-video-a-youtube)
6. [Troubleshooting](#6-troubleshooting)
7. [Referencia Técnica](#7-referencia-técnica)

---

## 1. Configuración Inicial

### ✅ Prerequisitos

Antes de empezar, asegúrate de tener:

#### A. Google Cloud Console
1. **Proyecto creado**: "NoCountry Video Processor" (o el nombre que usaste)
2. **APIs habilitadas**:
   - YouTube Data API v3 ✅
   - Google+ API ✅
3. **Credenciales OAuth 2.0**:
   - Client ID: `<TU_CLIENT_ID>.apps.googleusercontent.com`
   - Client Secret: `<TU_CLIENT_SECRET>`
   - Redirect URI: `http://localhost:3000/auth/callback`
4. **Publishing Status**: `Testing` (no Production)
5. **Test Users**: Tu email agregado en la lista

#### B. Variables de Entorno
Verifica que `backend/api/.env` tenga:
```bash
GOOGLE_CLIENT_ID=<TU_CLIENT_ID>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<TU_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

#### C. Sistema Local
- ✅ Docker Desktop corriendo
- ✅ Al menos 4GB RAM disponible
- ✅ Navegador web (Chrome/Firefox/Edge)

---

## 2. Preparar Ambiente Docker

### Paso 1: Limpiar ambiente anterior
```powershell
cd C:\Users\Daniela\Desktop\S02-26-Equipo-04-Web-App-Development\backend
docker compose down -v
```
⚠️ **Nota**: `-v` elimina los volúmenes (DB limpia para testing)

### Paso 2: Construir con nuevas dependencias
```powershell
docker compose build api
```
⏱️ **Tiempo**: ~3-5 minutos (instala google-api-python-client)

### Paso 3: Iniciar servicios
```powershell
# Iniciar DB, Redis, MinIO
docker compose up -d db redis minio

# Esperar 10 segundos
Start-Sleep -Seconds 10

# Aplicar migraciones
docker compose run --rm api alembic upgrade head

# Iniciar API
docker compose up -d api

# Verificar estado
docker compose ps
```

**✅ Resultado esperado:**
```
NAME       IMAGE         STATUS
postgres   postgres:15   Up
redis      redis:7       Up
minio      minio/minio   Up
fastapi    backend-api   Up (healthy)
```

### Paso 4: Verificar logs
```powershell
docker compose logs api --tail 30
```

**✅ Buscar estas líneas:**
- `🚀 NoCountry Video API v1.0.0`
- `✅ Redis connected`
- `🎉 Application startup complete`
- `Uvicorn running on http://0.0.0.0:8000`

---

## 3. Probar OAuth Flow (Swagger UI)

### 🌐 Abrir Swagger UI
1. Navegar a: **http://localhost:8000/docs**
2. Deberías ver todos los endpoints organizados por tags

---

### ✅ PASO 1: Health Check

**Verificar que el API funciona:**

1. Expandir: **GET /health**
2. Click: **"Try it out"**
3. Click: **"Execute"**

**✅ Respuesta esperada (200 OK):**
```json
{
  "status": "healthy"
}
```

---

### 🔑 PASO 2: Obtener URL de Autorización de Google

**Endpoint**: `GET /api/v1/auth/google/authorize`

1. Buscar en la sección **"Autenticación"**
2. Expandir: **GET /api/v1/auth/google/authorize**
3. Click: **"Try it out"**
4. Click: **"Execute"**

**✅ Respuesta (200 OK):**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=...",
  "state": "cpEqW9MkYXBjPjEIyBUuin3PvK0iFhj40A4jYj38LqY"
}
```

5. **COPIAR** la URL completa (desde `https://` hasta el final)
6. **COPIAR** el valor de `state` (lo necesitarás en el paso 4)

---

### 🌐 PASO 3: Autorizar con Google (Navegador)

**⚠️ IMPORTANTE: Hazlo rápido, el code expira en 10 minutos**

1. **Pegar la URL** copiada en una nueva pestaña del navegador
2. **Iniciar sesión** con tu cuenta de Google (la que agregaste como Test User)
3. Verás una pantalla:
   ```
   NoCountry Video Processor wants to access your Google Account
   
   This will allow NoCountry Video Processor to:
   ✅ See your primary Google Account email address
   ✅ See your personal info
   ✅ Manage your YouTube videos
   ✅ View your YouTube account
   ```
4. **Click en "Continuar"** o **"Allow"**
5. Serás redirigido a:
   ```
   http://localhost:3000/auth/callback?code=4/0AfrIepA...&scope=...&state=...
   ```
   ⚠️ **La página mostrará error** (localhost:3000 no existe), es normal ✅

6. **COPIAR el parámetro `code`** de la URL:
   - Es el texto largo que está entre `code=` y `&scope`
   - Ejemplo: `4/0AfrIepAuDLF-rBTFXkS_vx7CdF-xZ2-sBthHEvupV_14QIshZCZxD_ScI5NpxcfHLvemAQ`

---

### 🔐 PASO 4: Intercambiar Code por JWT Token

**Endpoint**: `POST /api/v1/auth/google/callback`

1. **Regresar a Swagger UI** (http://localhost:8000/docs)
2. Buscar en **"Autenticación"**
3. Expandir: **POST /api/v1/auth/google/callback**
4. Click: **"Try it out"**
5. **Reemplazar el Request body** con:
   ```json
   {
     "code": "PEGA_AQUI_EL_CODE_DEL_PASO_3",
     "state": "PEGA_AQUI_EL_STATE_DEL_PASO_2"
   }
   ```
6. Click: **"Execute"**

**✅ Respuesta esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3Mjc...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

7. **COPIAR el `access_token` COMPLETO** (es un string muy largo que empieza con `eyJ`)

📌 **Este token dura 7 días** (604800 segundos)

---

### 🔓 PASO 5: Autorizar Swagger UI con el JWT Token

**Ahora vas a "loguearte" en Swagger UI:**

1. En la **parte superior derecha** de Swagger UI, busca el botón **"Authorize"** 🔒 (candado)
2. Click en **"Authorize"**
3. Se abrirá un modal con **dos opciones**:
   - **OAuth2PasswordBearer** (para login tradicional) ❌ No uses este
   - **HTTPBearer** (para JWT tokens) ✅ Usa este

4. Busca la sección **"HTTPBearer (http, Bearer)"**
5. En el campo **"Value"**, pegar:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   ⚠️ **IMPORTANTE**: Debe empezar con `Bearer ` (con espacio después)

6. Click en **"Authorize"**
7. El candado se volverá **cerrado** 🔒✅
8. Click en **"Close"**

✅ **Ahora todos los endpoints protegidos usarán este token automáticamente**

---

## 4. Verificar Conexión YouTube

### 📺 PASO 6: Comprobar que YouTube está conectado

**Endpoint**: `GET /api/v1/youtube/status`

1. Buscar en la sección **"YouTube"**
2. Expandir: **GET /api/v1/youtube/status**
3. Click: **"Try it out"**
4. Click: **"Execute"**

⚠️ **Nota**: El candado 🔒 debe estar cerrado (autorizado en el paso 5)

**✅ Respuesta esperada (200 OK):**
```json
{
  "connected": true,
  "provider_username": null,
  "provider_user_id": "113822179860751389711",
  "token_expires_at": "2026-02-26T21:19:37.874339",
  "is_expired": false
}
```

**✅ Validaciones:**
- `connected` = `true` ✅
- `provider_user_id` tiene tu Google User ID ✅
- `token_expires_at` es una fecha futura (~1 hora) ✅
- `is_expired` = `false` ✅

❌ **Si obtienes error 401 "No YouTube tokens found":**
- Vuelve al Paso 2 y repite el OAuth flow
- Verifica que copiaste bien el code y state

---

## 5. Subir Video a YouTube

### 🎬 PASO 7: Publicar Video en YouTube

**Endpoint**: `POST /api/v1/youtube/publish/{video_id}`

#### A. Preparación: Obtener un video_id

**Opción 1: Verificar si tienes videos en la DB**
```powershell
docker compose exec db psql -U fastapi_user -d fastapi_db -c "SELECT id, original_filename, status, storage_path FROM videos LIMIT 5;"
```

**Opción 2: Subir un video nuevo primero**
- Usa el endpoint de upload de videos (si lo tienes implementado)
- O crea un video manualmente en la DB para testing

#### B. Publicar en YouTube (Swagger UI)

1. En Swagger UI, buscar sección **"YouTube"**
2. Expandir: **POST /api/v1/youtube/publish/{video_id}**
3. Click: **"Try it out"**
4. Completar los campos:

   **`video_id`** (en el path):
   ```
   550e8400-e29b-41d4-a716-446655440000
   ```
   ⬆️ Reemplazar con un UUID real de tu DB

   **Request body**:
   ```json
   {
     "title": "Mi Primer Video desde la API 🎉",
     "description": "Este video fue subido automáticamente usando la integración de YouTube OAuth de NoCountry Video Processor.\n\n#nocountry #automation #youtube",
     "privacy": "private"
   }
   ```
   
   📝 **Opciones de `privacy`**:
   - `"private"` - Solo tú lo ves (recomendado para testing) ✅
   - `"unlisted"` - Cualquiera con el link lo ve
   - `"public"` - Aparece en búsquedas y tu canal

5. Click: **"Execute"**

⏱️ **Espera**: La subida puede tardar 10 segundos a 2 minutos dependiendo del tamaño del video

---

### ✅ Respuestas Esperadas

#### A. Éxito (200 OK):
```json
{
  "success": true,
  "message": "Video publicado en YouTube exitosamente",
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "youtube_video_id": "dQw4w9WgXcQ",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Mi Primer Video desde la API 🎉",
  "privacy": "private",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg"
}
```

🎉 **¡ÉXITO! Tu video está en YouTube:**
1. Copia el `youtube_url`
2. Ábrelo en tu navegador
3. Verifica que sea tu video ✅

---

#### B. Errores Comunes

##### ❌ 404 Not Found
```json
{
  "detail": "Video 550e8400-... no encontrado"
}
```
**Causa**: El video_id no existe en tu DB  
**Solución**: Verifica el UUID correcto con la query del paso A

---

##### ❌ 403 Forbidden
```json
{
  "detail": "No tienes permiso para publicar este video"
}
```
**Causa**: El video pertenece a otro usuario  
**Solución**: Usa un video que hayas subido tú

---

##### ❌ 400 Bad Request - "Video aún no está listo"
```json
{
  "detail": "Video aún no está listo. Estado actual: PENDING"
}
```
**Causa**: El video aún no terminó de procesarse  
**Solución**: Espera a que el estado sea `COMPLETED` o `READY`

---

##### ❌ 400 Bad Request - "No tiene ruta de almacenamiento"
```json
{
  "detail": "Video no tiene ruta de almacenamiento"
}
```
**Causa**: El video no fue guardado en MinIO correctamente  
**Solución**: Verifica que el campo `storage_path` no sea NULL en la DB

---

##### ❌ 500 Internal Server Error - "No such file or directory"
```json
{
  "detail": "Error inesperado: [Errno 2] No such file or directory: '/tmp/...' "
}
```
**Causa**: El archivo no existe en MinIO  
**Solución**: 
1. Verifica que el video esté en MinIO: `docker compose exec minio mc ls minio/videos`
2. Verifica que `storage_path` sea correcto en la DB

---

##### ❌ 500 Internal Server Error - "Error al subir video a YouTube"
```json
{
  "detail": "Cuota de YouTube API excedida. Intenta más tarde."
}
```
**Causa**: Excediste el límite diario de YouTube API  
**Solución**: 
- Espera 24 horas (quota se resetea a medianoche PST)
- O aumenta la quota en Google Cloud Console

---

## 6. Troubleshooting

### 🔧 Problema: "403 You do not have access to this page" (Google)

**Causa**: Tu cuenta no está en la lista de Test Users o la app está en Production

**Solución**:
1. Ir a: https://console.cloud.google.com/apis/credentials/consent
2. Verificar que **Publishing status** = `Testing`
3. Scroll down a **"Test users"**
4. Click **"+ ADD USERS"**
5. Agregar tu email
6. **Esperar 5 minutos** y reintentar

---

### 🔧 Problema: "400 Invalid grant: code expired"

**Causa**: El authorization code solo dura 10 minutos

**Solución**: Volver al Paso 2 y obtener un nuevo code

---

### 🔧 Problema: "401 Unauthorized" en endpoints de YouTube

**Causa**: No hiciste el Paso 5 (Authorize en Swagger UI)

**Solución**:
1. Click en el botón **"Authorize"** (candado arriba a la derecha)
2. Usar la sección **HTTPBearer**
3. Pegar: `Bearer <tu_jwt_token>`

---

### 🔧 Problema: Swagger UI no muestra opción HTTPBearer

**Causa**: El código de `dependencies.py` no está actualizado

**Solución**:
```powershell
# Verificar que el código tenga HTTPBearer
docker compose exec api grep -n "HTTPBearer" /app/app/core/dependencies.py

# Si no aparece, rebuild:
docker compose down
docker compose build api
docker compose up -d
```

---

### 🔧 Problema: Docker no inicia el API

**Solución**:
```powershell
# Ver logs detallados
docker compose logs api --tail 50

# Reinicio completo
docker compose down -v
docker compose build --no-cache api
docker compose up -d
```

---

### 🔧 Problema: "Connection refused" a MinIO

**Causa**: MinIO no está corriendo o no tiene el bucket creado

**Solución**:
```powershell
# Verificar que MinIO esté corriendo
docker compose ps minio

# Crear bucket si no existe
docker compose exec minio mc mb minio/videos --ignore-existing
```

---

## 7. Referencia Técnica

### 📊 Arquitectura

```
Usuario → Swagger UI
         ↓
    FastAPI Endpoint
         ↓
   YouTubeUploadService
         ↓
    1. Verifica OAuth tokens
    2. Busca video en PostgreSQL
    3. Descarga video de MinIO
    4. Usa Google YouTube API
    5. Sube video a YouTube
    6. Retorna URL del video publicado
```

---

### 🔑 Scopes de OAuth

El token JWT tiene estos permisos de YouTube:
- `https://www.googleapis.com/auth/youtube.upload` - Subir videos
- `https://www.googleapis.com/auth/youtube` - Leer info del canal

---

### 📦 Dependencias Instaladas

```
google-api-python-client==2.116.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
```

---

### 🗄️ Tablas de Base de Datos

#### `oauth_tokens`
```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR (youtube/instagram),
    access_token VARCHAR,
    refresh_token VARCHAR,
    expires_at TIMESTAMP,
    provider_user_id VARCHAR
);
```

#### `videos`
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    original_filename VARCHAR,
    storage_path VARCHAR,
    status VIDEO_STATUS_ENUM,
    -- ... otros campos
);
```

---

### 📝 Endpoints Implementados

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/v1/auth/google/authorize` | Obtener URL de autorización | No |
| POST | `/api/v1/auth/google/callback` | Intercambiar code por JWT | No |
| GET | `/api/v1/youtube/status` | Verificar conexión YouTube | JWT Bearer |
| POST | `/api/v1/youtube/publish/{video_id}` | Publicar video en YouTube | JWT Bearer |

---

### 🔄 Renovación Automática de Tokens

El sistema **renueva automáticamente** los tokens expirados:
- Access token dura ~1 hora
- Refresh token es permanente
- Si el access token está expirado, se usa el refresh token automáticamente
- No necesitas hacer nada manual ✅

---

### 📊 Límites de YouTube API

**Cuota diaria**: 10,000 unidades por día (por proyecto de Google Cloud)

**Costo de operaciones**:
- Upload de video: 1,600 unidades
- List videos: 1 unidad
- Update video: 50 unidades

**Resultado**: Puedes subir ~6 videos por día con la cuota gratuita

Para aumentar: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

---

## ✅ Checklist de Testing Completo

Marca cada paso cuando lo completes:

**Configuración:**
- [ ] Google Cloud Console configurado (Testing mode, Test Users)
- [ ] Variables de entorno en `.env`
- [ ] Docker Desktop corriendo

**Ambiente:**
- [ ] `docker compose down -v` ejecutado
- [ ] `docker compose build api` completado
- [ ] `docker compose up -d` todos los servicios arriba
- [ ] Migraciones aplicadas
- [ ] Logs de API muestran "Application startup complete"

**OAuth Flow:**
- [ ] Health check retorna 200 OK
- [ ] URL de autorización generada
- [ ] Autorizado con Google (pantalla con permisos de YouTube)
- [ ] Code obtenido del redirect
- [ ] JWT token obtenido del callback
- [ ] Swagger UI autorizado con Bearer token

**YouTube:**
- [ ] Status retorna `connected: true`
- [ ] Video subido y procesado en DB (o usar test video)
- [ ] Publicación en YouTube ejecutada
- [ ] Video visible en canal de YouTube ✅

---

## 🎓 Para Aprender Más

- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)

---

## 🎉 ¡Felicitaciones!

Si completaste todos los pasos y tu video está en YouTube, **¡la integración funciona perfectamente!** 🚀

**Próximos pasos:**
1. Crear Pull Request para que el equipo revise
2. Agregar más test users en Google Cloud Console
3. Documentar para el equipo de frontend
4. Considerar agregar campos adicionales (tags personalizados, thumbnail custom, etc.)

---

**Última actualización**: Febrero 26, 2026  
**Versión**: 1.0.0  
**Autor**: NoCountry Backend Team
