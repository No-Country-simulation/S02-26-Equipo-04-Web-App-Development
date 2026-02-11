# Frontend Setup (Local)

Este directorio contiene la app web del equipo frontend.

## Stack

- React
- TypeScript
- Tailwind CSS
- Zustand
- Vite
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

2. Ajustar `VITE_API_BASE_URL` segun tu entorno local.

La configuracion base se centraliza en `src/config/env.ts`.

## Comandos utiles

```bash
npm run dev
npm run lint
npm run test
npm run build
```

## Flujo recomendado

1. Crear branch desde `develop` con prefijo `feature/frontend-...`.
2. Trabajar en cambios pequenos y hacer commits convencionales.
3. Validar local: lint + test + build.
4. Abrir PR hacia `develop`.
