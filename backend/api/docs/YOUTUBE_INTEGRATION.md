# Integración con YouTube

## 📋 Resumen

Implementación completa de integración con YouTube para publicar videos generados por la aplicación directamente en los canales de YouTube de los usuarios.

## 🎯 Características

- ✅ **Login con Google/YouTube**: Un solo flujo OAuth para autenticar con Google y obtener permisos de YouTube
- ✅ **Subida automática**: Los usuarios pueden publicar videos en su canal de YouTube con un click
- ✅ **Renovación de tokens**: Los tokens de acceso se renuevan automáticamente sin intervención del usuario
- ✅ **Privacidad configurable**: Los videos pueden publicarse como públicos, privados o no listados

## 🏗️ Arquitectura

```
Usuario → Frontend → Backend API → YouTube Data API v3
                         ↓
                   Base de Datos (oauth_tokens)
```

## 📦 Componentes Creados

### 1. Modelo `OAuthToken`
**Archivo:** `backend/api/app/models/oauth_token.py`

Modelo de base de datos para almacenar tokens OAuth de servicios externos (YouTube, Instagram, etc.).

**Campos principales:**
- `user_id`: FK a tabla users
- `provider`: "youtube", "instagram", etc.
- `access_token`: Token de acceso (corta duración: ~1h)
- `refresh_token`: Token de refresh (larga duración)
- `expires_at`: Timestamp de expiración
- `scope`: Permisos otorgados

**Métodos:**
- `is_expired()`: Verifica si el token está expirado

### 2. Migración de Alembic
**Archivo:** `backend/api/alembic/versions/6b7c8d9e0f1a_crear_tabla_oauth_tokens.py`

Crea la tabla `oauth_tokens` con:
- Índices en `user_id`, `provider`
- Índice único compuesto `(user_id, provider)`
- Foreign key a `users` con `ON DELETE CASCADE`

### 3. Google OAuth Service (Actualizado)
**Archivo:** `backend/api/app/services/google_oauth_service.py`

**Cambios:**
- Agregados scopes de YouTube:
  - `https://www.googleapis.com/auth/youtube.upload`
  - `https://www.googleapis.com/auth/youtube`
- Método `_save_or_update_oauth_token()`: Guarda tokens en DB
- Actualizado `authenticate_with_google()`: Guarda tokens después de login

### 4. YouTube Upload Service
**Archivo:** `backend/api/app/services/youtube_upload_service.py`

Servicio para subir videos a YouTube usando YouTube Data API v3.

**Métodos principales:**
- `upload_video()`: Sube un video con metadata
- `_get_valid_access_token()`: Obtiene token válido (renueva si está expirado)
- `_refresh_access_token()`: Renueva token usando refresh_token

**Parámetros de `upload_video()`:**
- `user_id`: ID del usuario
- `video_file_path`: Ruta del video (MinIO o local)
- `title`: Título del video
- `description`: Descripción
- `tags`: Lista de tags
- `category_id`: Categoría de YouTube (default: 22 = People & Blogs)
- `privacy_status`: "public", "private", "unlisted"

### 5. YouTube Endpoints
**Archivo:** `backend/api/app/api/v1/endpoints/youtube.py`

**Endpoints:**

#### `POST /api/v1/youtube/publish/{video_id}`
Publica un video en YouTube.

**Requiere:** Usuario autenticado con cuenta de YouTube conectada

**Response:**
```json
{
  "success": true,
  "message": "Video publicado en YouTube exitosamente",
  "youtube_video_id": "dQw4w9WgXcQ",
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "published_at": "2026-02-26T12:00:00"
}
```

#### `GET /api/v1/youtube/status`
Verifica si el usuario tiene YouTube conectado.

**Response:**
```json
{
  "connected": true,
  "provider_username": null,
  "provider_user_id": "123456789",
  "token_expires_at": "2026-02-26T13:00:00",
  "is_expired": false
}
```

## 🔄 Flujo Completo

### 1. Usuario conecta YouTube
```
1. Usuario hace clic en "Conectar YouTube"
2. Frontend → GET /api/v1/auth/google/login
3. Backend devuelve authorization_url
4. Usuario autoriza en Google (acepta permisos)
5. Google redirige → Frontend con code
6. Frontend → POST /api/v1/auth/google/callback {code}
7. Backend:
   - Intercambia code por tokens
   - Guarda access_token y refresh_token en oauth_tokens
   - Devuelve JWT de sesión
8. Usuario ya puede publicar en YouTube
```

### 2. Usuario publica video
```
1. Usuario selecciona video procesado
2. Click en "Publicar en YouTube"
3. Frontend → POST /api/v1/youtube/publish/{video_id}
4. Backend:
   - Verifica que usuario tiene tokens
   - Si token expiró, lo renueva automáticamente
   - Sube video a YouTube con metadata
   - Devuelve URL del video en YouTube
5. Frontend muestra link al video publicado
```

## 🔐 Seguridad

### Tokens OAuth
- **Access Token**: Se almacena en DB pero debería encriptarse en producción
- **Refresh Token**: Permite renovar access_token sin que usuario vuelva a login
- **Expiración**: Access tokens expiran en ~1 hora, se renuevan automáticamente

### Best Practices Implementadas
- ✅ CSRF protection con state token en OAuth
- ✅ Tokens tienen foreign key a users con ON DELETE CASCADE
- ✅ Verificación de expiración antes de cada uso
- ✅ Renovación automática sin exponer tokens al frontend
- ⚠️ **TODO:** Encriptar access_token y refresh_token en producción

## 📝 TODOs para Producción

1. **Encriptación de tokens**: Usar Fernet o similar para encriptar tokens en DB
2. **Integración con MinIO**: Descargar video de MinIO antes de subir a YouTube
3. **Integración con modelo Video**: Obtener metadata del video de la DB
4. **Resumable Upload**: Para videos > 5MB, implementar upload en chunks
5. **Manejo de cuotas**: YouTube tiene límites de API (10,000 units/day)
6. **Notificaciones**: Informar al usuario cuando el video está procesado en YouTube
7. **Actualizar modelo Video**: Agregar campos `youtube_video_id` y `youtube_url`

## 🧪 Testing

### Requisitos
1. Tener cuenta de Google
2. Crear aplicación en Google Cloud Console
3. Habilitar YouTube Data API v3
4. Configurar OAuth consent screen
5. Agregar redirect URI: `http://localhost:3000/auth/callback`

### Variables de Entorno
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

### Endpoints para Testing

1. **Conectar YouTube:**
   ```bash
   curl http://localhost:8000/api/v1/auth/google/login
   # Devuelve authorization_url → Abrir en navegador
   ```

2. **Verificar conexión:**
   ```bash
   curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/youtube/status
   ```

3. **Publicar video:**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/youtube/publish/VIDEO_UUID
   ```

## 📊 Base de Datos

### Migración
```bash
# Aplicar migración
docker-compose exec api alembic upgrade head

# Verificar tabla creada
docker-compose exec db psql -U postgres -d videoproc -c "\d oauth_tokens"
```

### Consultas Útiles
```sql
-- Ver tokens de un usuario
SELECT provider, expires_at, is_expired()
FROM oauth_tokens 
WHERE user_id = 'USER_UUID';

-- Tokens expirados
SELECT user_id, provider, expires_at
FROM oauth_tokens
WHERE expires_at < NOW();
```

## 🎓 Referencias

- [YouTube Data API v3 Docs](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Video Upload](https://developers.google.com/youtube/v3/guides/uploading_a_video)
- [YouTube API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)

## 👥 Equipo

**Feature desarrollada por:** Backend Team  
**Branch:** `backend-feature-youtube-oauth`  
**Commits:** 7 commits atómicos  
**Fecha:** 26 de febrero, 2026
