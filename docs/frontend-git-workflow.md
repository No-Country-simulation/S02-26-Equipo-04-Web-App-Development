# Flujo de trabajo frontend (Team Rules)

## Contexto del monorepo

- `backend/`: equipo backend.
- `frontend/`: equipo frontend.
- Base de integracion compartida: `develop`.

## Ramas

- `main`: estable, solo entra cuando se entrega.
- `develop`: integracion de features.
- `feature/frontend-<tema>`: trabajo diario frontend.
- `hotfix/<tema>`: arreglos urgentes sobre `main`.

Ejemplos:

- `feature/frontend-auth-ui`
- `feature/frontend-layout`
- `feature/frontend-api-client`

## Crear una feature branch

Siempre desde `develop`:

```bash
git checkout develop
git pull
git checkout -b feature/frontend-<tema>
```

## Commits

Usamos Conventional Commits en forma simple:

- `feat:` nueva funcionalidad
- `fix:` bugfix
- `chore:` tareas menores o setup
- `refactor:` refactor sin cambio funcional
- `docs:` documentacion
- `ci:` pipelines o workflows

Ejemplos:

- `feat: auth login screen`
- `chore: add eslint + prettier`
- `ci: add frontend lint test build workflow`

## Pull Requests

Reglas:

- PR siempre hacia `develop`.
- Ideal: al menos 1 reviewer.
- CI en verde antes de merge.
- Evitar PR gigantes (ideal 200 a 400 lineas de diff).
- Usar bitacora local basada en `docs/frontend-pr-log.template.md`.

Para crearla en local:

```bash
cp docs/frontend-pr-log.template.md docs/frontend-pr-log.md
```

## Vida util de ramas

- Feature branches: 1 a 3 dias, merge rapido.
- Si crece mucho, dividir en sub-features.

## Sincronizacion con develop

Antes de abrir PR:

```bash
git checkout develop
git pull
git checkout feature/frontend-<tema>
git rebase develop
```

Alternativa simple si el equipo evita rebase:

```bash
git merge develop
```

## Resolucion de conflictos

1. Resolver conflictos en local.
2. Correr checks locales.
3. Push de la rama y avisar en el PR.

Checks sugeridos:

```bash
cd frontend
npm run lint
npm run test
npm run build
```
