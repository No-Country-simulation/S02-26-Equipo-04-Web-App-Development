# Estructura de carpetas frontend

Guia rapida para que cualquier dev junior entienda donde crear codigo nuevo en este proyecto.

## Vista general

```text
frontend/
  docs/
  src/
    config/
    pages/
    router/
    store/
    App.tsx
    index.css
    main.tsx
```

## Que va en cada carpeta

- `src/pages/`: vistas completas por ruta (landing, login, register, home privada).
- `src/router/`: configuracion de rutas, guards y helpers de redireccion.
- `src/store/`: estado global con Zustand (auth, preferencias, etc.).
- `src/config/`: configuraciones del entorno y constantes base.
- `src/index.css`: estilos globales, `@theme` de Tailwind v4 y tokens Tokyo Night.

## Convenciones recomendadas

- Un archivo por componente principal.
- Nombres de componentes en PascalCase (`LoginPage.tsx`).
- Helpers y utilidades en camelCase (`redirects.ts`).
- Commits pequenos y atomicos, con Conventional Commits.

## Como agregar una nueva feature

1. Crear branch desde `develop`: `feature/frontend-<tema>`.
2. Crear pagina en `src/pages/` si la feature necesita ruta nueva.
3. Registrar ruta en `src/router.tsx`.
4. Si necesita estado compartido, crear store en `src/store/`.
5. Validar local en `frontend/`:

```bash
npm run lint
npm run test
npm run build
```

## Recomendacion para PRs

- Incluir lista corta de archivos clave modificados.
- Explicar que problema se resolvio y como se valida.
- Copiar el resumen desde `docs/frontend-pr-log.md` al crear el PR.
