# 🚀 Guía Backend 🐳 

## 📁 Estructura del proyecto
```
project-root/
│
├── docker-compose.yml
│
├── api/
│   ├── Dockerfile          
│   ├── requirements.txt
│   └── main.py
│
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
└── README.md
```

## Flujo de la App:

           ┌────────────┐
           │   API      │
           └────┬───────┘
                │ crea job
                ▼
           ┌────────────┐
           │  Postgres  │
           └────┬───────┘
                │ job id
                ▼
           ┌────────────┐
           │   Redis    │ ← cola
           └────┬───────┘
                ▼
           ┌────────────┐
           │  Worker    │
           └──────────┬─┘
                      │ ← actualiza DB
                      ▼
                   ┌────────────┐
                   │  Postgres  │
                   └────────────┘
  


## 🧩 Servicios

| Servicio      | Puerto | Función                |
| ------------- | ------ | ---------------------- |
| API (FastAPI) | 8000   | Backend principal      |
| Postgres      | 5432   | Base de datos          |
| Redis         | 6379   | Cola / cache           |
| Worker        | —      | Procesamiento de video |

## 🌍 Endpoints de prueba
| URL                                                    | Función              |
| ------------------------------------------------------ | -------------------- |
| [http://localhost:8000](http://localhost:8000)         | Health check         |
| [http://localhost:8000/env](http://localhost:8000/env) | Estado de DB y Redis |


# Instalar y configurar

## 📋 Requisitos previos
- Docker Desktop instalado y corriendo
- Postman instalado (o usar el navegador para algunos endpoints)
- Git configurado

---

## 1️⃣ Clonar y preparar el proyecto

```bash
# Clonar el repositorio (si aún no lo tienen)
git clone https://github.com/No-Country-simulation/S02-26-Equipo-04-Web-App-Development.git
cd S02-26-Equipo-04-Web-App-Development

# Cambiar a la rama de desarrollo
git checkout feature/auth-usuario
git pull origin feature/auth-usuario

# Ir a la carpeta backend
cd backend
```

---

## 2️⃣ Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cd api
cp .env.example .env
```

**Opcional:** Editar `.env` si quieren cambiar alguna configuración (por defecto funciona bien).

---

## 3️⃣ Levantar los contenedores Docker

```bash
# Volver a la carpeta backend
cd ..

# Levantar todos los servicios
docker-compose up -d

# Ver que todos los contenedores estén corriendo
docker-compose ps
```

**Deberían ver:**
- ✅ `fastapi` - API corriendo en puerto 8000
- ✅ `postgres` - Base de datos en puerto 5432
- ✅ `redis` - Cache en puerto 6379
- ✅ `minio` - Almacenamiento en puerto 9000

---

## 4️⃣ Aplicar las migraciones de la base de datos

```bash
# Ejecutar la migración de Alembic
docker exec -it fastapi alembic upgrade head
```

**Deberían ver:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 1d11381e9cfe, add profiles table and restructure user model
```

---

## 5️⃣ Verificar que la API está corriendo

Abrir el navegador en: **http://localhost:8000/docs**

Deberían ver la documentación interactiva de Swagger con todos los endpoints disponibles.

---

## 6️⃣ Probar los endpoints en Postman

### 📍 **Endpoint 1: Health Check**

**GET** `http://localhost:8000/health`

**Respuesta esperada:**
```json
{
  "status": "healthy"
}
```

---

### 📍 **Endpoint 2: Registrar un usuario**

**POST** `http://localhost:8000/api/v1/auth/register`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "usuario@example.com",
  "password": "MiPassword123"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**✨ Lo que pasó internamente:**
- Se creó un usuario en la tabla `users` con role `USER`
- Se creó automáticamente un perfil vacío en la tabla `profiles`

---

### 📍 **Endpoint 3: Login**

**POST** `http://localhost:8000/api/v1/auth/login`

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Body (x-www-form-urlencoded):**
```
username=usuario@example.com
password=MiPassword123
```

**Respuesta esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**💡 Importante:** Copien el `access_token` para usarlo en los siguientes endpoints.

---

### 📍 **Endpoint 4: Obtener información del usuario actual**

**GET** `http://localhost:8000/api/v1/auth/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

(Reemplazar `{access_token}` con el token que copiaron)

**Respuesta esperada (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "role": "USER",
  "is_active": true,
  "is_verified": false
}
```

---

### 📍 **Endpoint 5: Logout**

**POST** `http://localhost:8000/api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Respuesta esperada (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

## 7️⃣ Ver los datos en la base de datos

### Opción A: Desde la terminal (PostgreSQL CLI)

```bash
# Conectarse a PostgreSQL
docker exec -it postgres psql -U postgres -d fastapi_db

# Ver las tablas
\dt

# Ver usuarios registrados
SELECT id, email, role, is_active, is_verified, is_banned, created_at FROM users;

# Ver perfiles creados
SELECT user_id, display_name, full_name, preferred_language, timezone, created_at FROM profiles;

# Ver la relación User-Profile
SELECT u.email, u.role, p.display_name, p.preferred_language 
FROM users u 
LEFT JOIN profiles p ON u.id = p.user_id;

# Salir
\q
```

### Opción B: Usar un cliente gráfico (DBeaver, pgAdmin, TablePlus)

**Configuración de conexión:**
- **Host:** `localhost`
- **Puerto:** `5432`
- **Base de datos:** `fastapi_db`
- **Usuario:** `postgres`
- **Contraseña:** `postgres`

---

## 8️⃣ Casos de prueba adicionales

### ✅ Probar validaciones

**Email inválido:**
```json
{
  "email": "no-es-un-email",
  "password": "MiPassword123"
}
```
**Esperado:** Error 422 (Validation Error)

---

**Password muy corta:**
```json
{
  "email": "test@example.com",
  "password": "123"
}
```
**Esperado:** Error 422 o 400 (según validación configurada)

---

**Usuario duplicado:**
Intentar registrar el mismo email dos veces.
**Esperado:** Error 400 (Email already registered)

---

**Token inválido:**
Llamar a `/auth/me` con un token inventado.
**Esperado:** Error 401 (Unauthorized)

---

## 9️⃣ Comandos útiles Docker

```bash
# Ver logs de la API
docker logs fastapi -f

# Ver logs de la base de datos
docker logs postgres -f

# Reiniciar solo la API
docker-compose restart fastapi

# Parar todos los contenedores
docker-compose down

# Parar Y BORRAR la base de datos (empezar desde cero)
docker-compose down -v

# Ver contenedores corriendo
docker-compose ps

# Ver recursos consumidos
docker stats
```

---

## 🔟 Estructura de las tablas

### Tabla `users` (Autenticación)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Primary key |
| email | String | Único, para login |
| hashed_password | String | Password encriptado con bcrypt |
| role | Enum | USER o ADMIN |
| is_active | Boolean | Usuario activo |
| is_verified | Boolean | Email verificado |
| is_banned | Boolean | Usuario baneado |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Última actualización |

### Tabla `profiles` (Datos personales)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| user_id | UUID | Primary key & Foreign key a users.id |
| display_name | String | Nombre para mostrar |
| full_name | String | Nombre completo |
| birth_date | Date | Fecha de nacimiento |
| bio | Text | Biografía |
| avatar_url | String | URL del avatar |
| preferred_language | String | Idioma preferido (default: "es") |
| timezone | String | Zona horaria (default: "UTC") |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Última actualización |

**Relación:** 1 User → 1 Profile (CASCADE on delete)

---

## 🐛 Troubleshooting

### Error: "Port already in use"
```bash
# Ver qué está usando el puerto 8000
netstat -ano | findstr :8000

# Matar el proceso (reemplazar PID)
taskkill /PID <numero> /F

# O cambiar el puerto en docker-compose.yml
```

### Error: "Database does not exist"
```bash
# Recrear la base de datos
docker-compose down -v
docker-compose up -d
docker exec -it fastapi alembic upgrade head
```

### Error: "Alembic migration failed"
```bash
# Ver el estado de las migraciones
docker exec -it fastapi alembic current

# Ver historial
docker exec -it fastapi alembic history

# Aplicar todas las migraciones pendientes
docker exec -it fastapi alembic upgrade head
```

### La API no responde
```bash
# Ver logs para ver el error
docker logs fastapi

# Reiniciar el contenedor
docker-compose restart fastapi
```

---

## 📚 Recursos adicionales

- **Documentación Swagger:** http://localhost:8000/docs
- **Redoc (alternativa):** http://localhost:8000/redoc
- **MinIO Console:** http://localhost:9001 (usuario: `minio`, password: `miniopass`)

---

## 🔐 Pruebas de Google OAuth 2.0

### 📋 Requisitos previos
- Tener las credenciales de Google OAuth configuradas en `.env`
- El archivo `.env` debe tener:
  ```bash
  GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=tu-client-secret
  GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
  ```
  
**⚠️ IMPORTANTE:** Las credenciales reales están en el archivo `.env` (que NO se sube a GitHub). Si necesitas las credenciales, pídelas al equipo por Discord.

### 📍 **Paso 1: Generar URL de autorización de Google**

**GET** `http://localhost:8000/api/v1/auth/google/login`

**Headers:** Ninguno requerido

**Respuesta esperada:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "state": "X5Ib5JJ0MtsMAsxzUOeVq-tDHhtQUVV75mpHrIdTL-c"
}
```

**⚠️ IMPORTANTE:** Guarda el valor de `state` para el siguiente paso.

---

### 📍 **Paso 2: Autenticarse con Google (manual)**

1. **Copia la URL** completa de `authorization_url` del paso anterior
2. **Pégala en tu navegador** y presiona Enter
3. **Selecciona tu cuenta de Google** y autoriza la aplicación
4. **Google te redirigirá** a una URL como:
   ```
   http://localhost:3000/auth/callback?state=X5Ib5JJ0...&code=4/0AfrIepD...&scope=email+profile...
   ```
5. **Copia el valor del parámetro `code`** de la URL (después de `code=` y antes de `&scope`)

**Ejemplo:**
```
code=4/0AfrIepDwG5Ab2OCYRUj2Amksvdqg2xP67ifOA8KyKb9wY0cYAO_tmxJTLr1xzV9IoOLEDw
```

---

### 📍 **Paso 3: Completar el flujo OAuth (callback)**

**POST** `http://localhost:8000/api/v1/auth/google/callback`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "code": "4/0AfrIepDwG5Ab2OCYRUj2Amksvdqg2xP67ifOA8KyKb9wY0cYAO_tmxJTLr1xzV9IoOLEDw",
  "state": "X5Ib5JJ0MtsMAsxzUOeVq-tDHhtQUVV75mpHrIdTL-c"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "d238830f-a5dd-4691-85fd-dd6d1a1b567f",
    "email": "tuusuario@gmail.com",
    "role": "USER",
    "is_active": true,
    "is_verified": true
  }
}
```

**⚠️ NOTA:** El código de Google (`code`) **expira en 10 minutos** y es de **un solo uso**. Si falla, debes repetir desde el Paso 1.

---

### 📍 **Verificar usuario en la base de datos**

```bash
# Conectarse a la base de datos
docker exec -it postgres psql -U postgres -d fastapi_db

# Ver usuarios creados con Google OAuth
SELECT id, email, provider, provider_user_id, is_verified FROM users WHERE provider='google';

# Salir de psql
\q
```

**Deberías ver:**
```
                  id                  |         email         | provider | provider_user_id | is_verified
--------------------------------------+-----------------------+----------+------------------+-------------
 d238830f-a5dd-4691-85fd-dd6d1a1b567f | tuusuario@gmail.com   | google   | 1234567890       | t
```

---

### 🧪 **Prueba avanzada: PowerShell (automatizada)**

Si usas Windows con PowerShell, puedes probar todo el flujo así:

```powershell
# 1. Generar URL de autorización
$response = Invoke-WebRequest -Uri http://localhost:8000/api/v1/auth/google/login -Method GET -UseBasicParsing | ConvertFrom-Json
Write-Host "URL: $($response.authorization_url)"
Write-Host "State: $($response.state)"

# 2. Abre la URL en el navegador, autentica con Google, y copia el 'code' de la URL de callback

# 3. Enviar el código al callback
$code = "TU_CODIGO_AQUI"
$state = $response.state
$body = @{ code = $code; state = $state } | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/api/v1/auth/google/callback -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

---

### ✅ **Validaciones del flujo OAuth**

Después de completar el flujo, verifica:

- [ ] El endpoint `/auth/google/login` genera una URL válida
- [ ] Google redirige correctamente después de autenticar
- [ ] El endpoint `/auth/google/callback` devuelve un JWT válido
- [ ] El usuario se crea en la tabla `users` con `provider='google'`
- [ ] El perfil del usuario se crea automáticamente en la tabla `profiles`
- [ ] El campo `hashed_password` del usuario OAuth es `NULL`
- [ ] El campo `is_verified` es `true` (porque Google ya verificó el email)
- [ ] El `access_token` funciona para acceder a endpoints protegidos

---

### 🔧 **Troubleshooting OAuth**

**Error: "Error en el servidor remoto: (400) Solicitud incorrecta"**
- El código de Google expiró (dura 10 minutos)
- Solución: Genera una nueva URL desde el Paso 1

**Error: "Error en autenticación con Google: ..."**
- Verifica que las credenciales en `.env` sean correctas
- Verifica que `docker-compose restart fastapi` se ejecutó después de cambiar `.env`

**El usuario no se crea en la base de datos**
- Verifica que la migración de Alembic esté aplicada: `docker exec -it fastapi alembic upgrade head`
- Chequea los logs: `docker logs fastapi --tail 50`

---

## ✅ Checklist de verificación

### Configuración inicial:
- [ ] Docker Desktop está corriendo
- [ ] `docker-compose up -d` ejecutado sin errores
- [ ] Migración de Alembic aplicada (`alembic upgrade head`)
- [ ] http://localhost:8000/docs responde

### Autenticación tradicional (email/password):
- [ ] Registro de usuario funciona
- [ ] Login funciona y devuelve token
- [ ] `/auth/me` funciona con el token
- [ ] Los datos se guardan en la base de datos (verificado con `psql`)
- [ ] Tablas `users` y `profiles` existen y tienen la relación correcta

### Autenticación con Google OAuth:
- [ ] Credenciales de Google configuradas en `.env`
- [ ] `/auth/google/login` genera URL de autorización
- [ ] Google redirige correctamente después de autenticar
- [ ] `/auth/google/callback` devuelve JWT válido
- [ ] Usuario OAuth se crea con `provider='google'`
- [ ] Perfil se crea automáticamente para usuario OAuth
- [ ] JWT de usuario OAuth funciona en endpoints protegidos

---

## 📞 ¿Problemas?

Si tienen algún error que no puedan resolver:
1. Copien el mensaje de error completo
2. Copien los logs: `docker logs fastapi`
3. Compartan en el canal de Discord del equipo

---
