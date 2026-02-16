# Frontend PR Log

## 2026-02-16

### frontend-video-upload-test - home base + UI minima reutilizable
- Se crea la rama `frontend-video-upload-test` desde `develop` para trabajar la estructura base del home (upload + filtros + resultados) y componentes UI reutilizables.
- Alcance inicial: `Button`, `Input`, `Card/Panel`, `Loader` y sus skeletons para estados de carga (`empty/loading/error`) en mobile y desktop.
- Los componentes base se centralizan en `src/components/ui/`; los skeletons especificos de vista se ubican junto a la feature (por ejemplo, `src/components/home/`).

## 2026-02-15

### auth/login - manejo de errores y visibilidad de password
- Se mejora el mensaje de error en login para evitar mostrar `Failed to fetch` cuando falla la validacion de credenciales o hay error de red.
- Se agrega boton con icono de Lucide (`Eye` / `EyeOff`) para mostrar u ocultar la contraseña en la pantalla de login.
- Se ajusta `autoComplete` del campo password a `current-password` para mejorar la experiencia de autocompletado.
