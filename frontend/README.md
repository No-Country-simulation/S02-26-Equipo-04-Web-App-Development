# Frontend Setup (Local)

Este directorio contiene la app web del equipo frontend.

## Stack

- Next.js
- TypeScript
- Tailwind CSS
- Zustand
- Lucide React
- Vitest

## Requisitos

- Node.js 20+
- npm 10+

## Instalacion

```bash
npm install
```

## Variables de entorno

1. Copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

2. Ajustar `NEXT_PUBLIC_API_BASE_URL` segun tu entorno local.

La configuracion base se centraliza en `src/config/env.ts`.

## Tailwind CSS v4

- El proyecto usa `tailwindcss@4` con el plugin oficial `@tailwindcss/postcss`.
- La importacion de Tailwind se hace en `src/app/globals.css` con `@import "tailwindcss";`.
- Los tokens de tema se definen en `src/app/globals.css` dentro de `@theme`.
- No usamos `tailwind.config.ts` ni `postcss.config.js` en esta version.

## Comandos utiles

```bash
npm run dev
npm run lint
npm run test
npm run build
npm run start
```

## Flujo recomendado

1. Crear branch desde `develop` con prefijo `feature/frontend-...`.
2. Trabajar en cambios pequenos y hacer commits convencionales.
3. Validar local: lint + test + build.
4. Abrir PR hacia `develop`.

## Arquitectura de carpetas (hibrida por dominio)

Base recomendada para crecer sin mezclar responsabilidades:

- `src/app/`: rutas de Next (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`).
- `src/components/ui/`: componentes visuales globales y reutilizables (`Button`, `Input`, `Card`).
- `src/components/layout/`: piezas de layout compartidas (barra superior, sidebar, wrappers).
- `src/features/<dominio>/`: codigo por dominio (ej: `auth`, `jobs`, `uploads`) para UI + hooks + logica propia.
- `src/services/`: acceso a APIs externas.
- `src/store/`: estado global (Zustand).
- `src/config/`: variables de entorno y configuracion.
- `src/router/`: reglas de redireccion y utilidades de navegacion.

Regla rapida:

- Si se usa en mas de una pagina -> `src/components/`.
- Si es exclusivo de una ruta -> puede vivir dentro de `src/app/<ruta>/components/`.

### Que NO conviene hacer

- No meter componentes globales dentro de `src/app/`.
- No mezclar llamadas HTTP dentro de componentes visuales (usar `src/services/`).
- No duplicar estilos de botones/inputs por pagina si ya existe componente reusable.
- No poner logica de redireccion hardcodeada en varias pantallas si ya hay helper en `src/router/`.
