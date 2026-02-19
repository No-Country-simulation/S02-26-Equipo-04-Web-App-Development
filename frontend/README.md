# Frontend Setup (Local)

Este directorio contiene la app web del equipo frontend.

## Stack

- Next.js
- TypeScript
- Tailwind CSS
- Zustand
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
