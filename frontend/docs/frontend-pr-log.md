# Frontend PR Log

## 2026-02-15

### auth/login - manejo de errores y visibilidad de password
- Se mejora el mensaje de error en login para evitar mostrar `Failed to fetch` cuando falla la validacion de credenciales o hay error de red.
- Se agrega boton con icono de Lucide (`Eye` / `EyeOff`) para mostrar u ocultar la contraseña en la pantalla de login.
- Se ajusta `autoComplete` del campo password a `current-password` para mejorar la experiencia de autocompletado.
