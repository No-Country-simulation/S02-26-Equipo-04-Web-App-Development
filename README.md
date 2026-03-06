# S02-26-Equipo-04-Web-App-Development

## Objetivo

Este proyecto busca automatizar la generacion de videos verticales a partir de videos horizontales, manteniendo la informacion relevante en pantalla y optimizando el encuadre para presencia constante en redes sociales.

## Estructura del monorepo

- `backend/`: APIs, procesamiento y servicios de infraestructura.
- `frontend/`: aplicacion web (React + TypeScript + Tailwind + Zustand).
- `docs/`: guias de trabajo para el equipo.

## Documentacion de equipo frontend

- Guia de ramas y PRs: `docs/frontend-git-workflow.md`
- Template de bitacora para PR a `develop`: `docs/frontend-pr-log.template.md`
- Setup local frontend: `frontend/README.md`
-   

## 1️⃣ Introducción         
![IMagen1](https://res.cloudinary.com/dpiwmbsog/image/upload/v1771258428/haceloCorto/hacelocorto_dqnlnr.png)

### 1.1 Contexto

Para lograr mayor visibilidad, autoridad y generar networking en redes sociales con el objetivo de incrementar ventas, actualmente es necesario producir contenido audiovisual en formato horizontal y shorts derivados del mismo.

Para startups, pymes y emprendedores, la generación constante de este tipo de contenido representa una demanda significativa de tiempo, desviando recursos del core del negocio.                           

### 1.2 Propósito del Sistema

El presente proyecto tiene como finalidad desarrollar una solución tecnológica que permita:

- Optimizar la generación de contenido audiovisual.
- Facilitar la gestión y automatización del proceso.
- Reducir el tiempo operativo invertido por el cliente.
- Mejorar la presencia digital y escalabilidad comercial.

***
## 2️⃣ Objetivos
### 2.1 Objetivo General
Desarrollar una aplicación web que permita gestionar y optimizar la producción y administración de contenido audiovisual para redes sociales.

### 2.2 Objetivos Específicos
- Implementar una arquitectura escalable y mantenible.
- Separar responsabilidades entre frontend y backend.
- Diseñar una base de datos estructurada y normalizada.
- Garantizar seguridad y control de accesos.
- Permitir futuras integraciones con plataformas externas.
***
## 3️⃣ Alcance del Proyecto
### 3.1 Incluye
- Desarrollo de frontend.
- Desarrollo de backend.
- Diseño e implementación de base de datos.
- Integración entre servicios.
- Despliegue en entorno productivo.
***
## 4️⃣ Arquitectura del Proyecto
- El sistema sigue un modelo de Arquitectura Cliente-Servidor, donde el frontend y el backend se comunican a través de una API RESTful desarrollada con FastAPI.
- Frontend (Cliente):
Responsable de la interfaz de usuario y la interacción con el sistema, consume los endpoints REST expuestos por el backend.
- Backend (Servidor / API):
Implementado con una arquitectura en capas, separando responsabilidades de forma clara y mantenible

### 4.1 Diagrama General de Arquitectura

![Arquitectura Backend](https://res.cloudinary.com/dxf0uxwre/image/upload/v1772550803/arquitectura-backend_dtetbv.png)

El diagrama muestra la arquitectura del Backend. Elegimos crear 2 nodos desacoplados para separar responsabilidades y mejorar escalabilidad y rendimiento.
- El nodo 1 (FastAPI + Redis + PostgreSQL) gestiona los endpoints, valida datos, persiste información y publica tareas asincrónicas en Redis.
- El nodo 2 (Video processing) consume esas tareas y ejecuta el procesamiento pesado de manera independiente.

Motivos principales:
1. Evitar que procesos largos bloqueen la API.
2. Responder rápido al cliente mientras el trabajo se ejecuta en segundo plano.
3. Escalar API y Video processing de forma independiente.
4. Mejorar tolerancia a fallos y uso eficiente de recursos.

Esto nos permite un sistema más modular, escalable y robusto para procesamiento de video.

### 4.2 Backend
Tecnologías Utilizadas

- FastAPI - Framework web moderno para Python, API REST
- PostgreSQL - Base de datos relacional para persistencia
- Redis - Sistema de colas para procesamiento asíncrono de tareas
- MinIO - Almacenamiento de objetos S3-compatible para videos y archivos
- OpenCV - Procesamiento y análisis de videos
- FFmpeg 7.1 - Codificación y manipulación de videos
- Docker & Docker Compose - Containerización y orquestación

Responsabilidades del Backend
- Gestión de lógica de negocio.
- Exposición de API REST.
- Recepción y validación de videos.
- Análisis de video para identificación de rostros/orador principal.
- Generación de recortes de video y paneo automático.
- Autenticación y autorización.
- Persistencia de datos.
- Validaciones y seguridad.

### 4.3 Frontend
Tecnologías Utilizadas

- React (v19)
- React Router 7
- Tailwind CSS v4.1
- Zustand: Gestión de estado ligero

UI, Iconos y Animaciones
- Lucide React: Librería de iconos
- Framer Motion: Animaciones y gestos - Recomendado para transiciones suaves entre vídeos y

Responsabilidades del Frontend

- Interfaz de usuario.
- Consumo de API.
- Gestión de estado.
- Validaciones del lado del cliente.
- Experiencia de usuario (UX/UI).
***
## 5️⃣ Base de Datos
### 5.1 Modelo de Datos
El modelo de base de datos fue diseñado siguiendo principios de normalización y escalabilidad.

Tipo de Base de Datos: PostgreSQL
> 🔗 Diagrama de base de datos: https://dbdiagram.io/d/equipo4-69874319bd82f5fce2f7e80b

![Diagrama-DB](https://res.cloudinary.com/dxf0uxwre/image/upload/v1772550723/esquema_db_ecahyv.png)

### 5.2 Consideraciones Técnicas
- Relaciones normalizadas.
- Integridad referencial.
- Índices para optimización de consultas.
- Preparada para escalabilidad futura.
***
## 6️⃣ Flujo de Funcionamiento

- El usuario accede a la plataforma y realiza una acción desde la interfaz.
- El frontend envía una solicitud HTTP al backend a través de la API REST.
- El backend valida los datos, procesa la lógica de negocio y consulta o modifica la base de datos según corresponda.
- Se consulta o modifica información en la base de datos.
- El backend retorna una respuesta estructurada al frontend.
- La interfaz se actualiza dinámicamente reflejando el resultado de la operación.
***
## 7️⃣ Setup y Configuración
### 7.1 Requisitos Previos
- Python >= 3.12.3
- pip (gestor de paquetes de Python)
- PostgreSQL (base de datos) 
- Redis (caché) 
- Docker y Docker Compose (para ejecutar servicios)
- Variables de entorno configuradas 

### 7.2 Instalación Backend
Nota:
![Comandos](https://i.imgur.com/wBjrXgU.jpg)

- Clonar el repositorio
- git clone https://github.com/No-Country-simulation/S02-26-Equipo-04-Web-App-Development.git
- cd backend
- python3 -m venv venv
- source venv/bin/activate  # En Linux/Mac
- venv\Scripts\activate  # En Windows
- pip install -r requirements.txt
- cp .env.example .env
- alembic upgrade head
- python3 -m uvicorn app.main:app --reload

## Para ejecutar con Docker:

- git clone https://github.com/No-Country-simulation/S02-26-Equipo-04-Web-App-Development.git
- cd backend

### Configurar variables de entorno
- cp .env.example .env
### Editar .env con tus datos

### Construir y ejecutar los servicios
- docker-compose up -d

### Ejecutar migraciones (opcional si el contenedor las hace automáticamente)
- docker-compose exec api alembic upgrade head

### Ver logs del servidor
- docker-compose logs -f api

### 7.3 Instalación Frontend
- git clone [URL repositorio]
- cd frontend
- npm install
- npm run dev
***

## 8️⃣Equipo de Desarrollo
- Lucas Matias Segovia - Project Manager [Linkedin](https://www.linkedin.com/in/lumseg/)
- Agustin Nazer - Dev Backend [Linkedin](https://www.linkedin.com/in/agustinnazer)
- Matias Nehuen Malpartida - Dev Backend [Linkedin](https://www.linkedin.com/in/matiasnm)
- Daniela Homobono - Dev Backend [Linkedin](https://www.linkedin.com/in/daniela-homobono)
- Amaro Ferraris - DevOps [Linkedin](https://www.linkedin.com/in/amaroferraris)
- Neculqueo Guillermo Agustín - Dev Frontend [Linkedin]()
- Marcos Benegas - Dev Frontend [Linkedin](https://www.linkedin.com/in/marcos-ezequiel-benegas/)
