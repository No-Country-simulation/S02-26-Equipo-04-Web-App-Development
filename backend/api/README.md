# NoCountry Video API

API para procesamiento automático de videos (horizontal → vertical shorts)

## Stack Tecnológico

- **Runtime**: Python 3.11
- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)

## Estructura del Proyecto

```
api/
├── app/
│   ├── core/           # Configuración central
│   ├── database/       # Data Access Layer
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── api/v1/         # API endpoints
│   ├── services/       # Business Logic
│   ├── repositories/   # Data access patterns
│   └── utils/          # Utilidades
├── alembic/            # Migraciones de DB
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Setup Local

### 1. Crear archivo .env

```bash
cp .env.example .env
```

Editar `.env` y configurar las variables necesarias.

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar migraciones

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Iniciar servidor

```bash
uvicorn app.main:app --reload
```

## Setup con Docker

### 1. Construir imagen

```bash
docker-compose build --no-cache api
```

### 2. Levantar servicios

```bash
docker-compose up -d
```

### 3. Ver logs

```bash
docker-compose logs -f api
```

### 4. Ejecutar migraciones

```bash
docker exec -it fastapi bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Testing de Endpoints

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Registro

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "full_name": "Test User"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=TestPassword123"
```

### Obtener Perfil

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <TOKEN>"
```

## Documentación Interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Comandos Útiles

```bash
# Reconstruir sin cache
docker-compose build --no-cache api

# Entrar al contenedor
docker exec -it fastapi bash

# Ver logs de PostgreSQL
docker-compose logs -f db

# Ver logs de Redis
docker-compose logs -f redis

# Verificar tablas en DB
docker exec -it postgres psql -U postgres -d fastapi_db -c "\dt"
```
