# Frontend PR Worklog

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feature/i18n-multidioma`

### Objetivo

Incorporar infraestructura de internacionalizacion en Next.js (es/en) y aplicar una primera ronda completa en landing, auth y shell del dashboard sin romper el flujo actual de rutas.

### Cambios implementados en curso

- Se integro `next-intl` en `frontend/next.config.ts` con `request config` en `frontend/src/i18n/request.ts` y locales base en `frontend/src/i18n/locales.ts`.
- Se agregaron catálogos iniciales en `frontend/src/messages/es.json` y `frontend/src/messages/en.json` para `common`, `auth` y `dashboard`.
- Se incorporo `LanguageSwitcher` global en `frontend/src/components/i18n/LanguageSwitcher.tsx` con persistencia de `NEXT_LOCALE` via server action en `frontend/src/app/actions/setLocale.ts`.
- Se adapto `frontend/src/app/layout.tsx` para envolver la app con `NextIntlClientProvider` y resolver metadata base dinamica por locale (`es_AR`/`en_US`).
- Se internacionalizo `frontend/src/app/page.tsx` (landing) incluyendo metadata SEO/OpenGraph/Twitter por idioma y traduccion completa de secciones visibles.
- Se internacionalizaron pantallas de autenticacion en `frontend/src/app/auth/login/page.tsx`, `frontend/src/app/auth/register/page.tsx` y `frontend/src/app/auth/callback/GoogleCallbackClient.tsx`.
- Se internacionalizo el shell principal del dashboard en `frontend/src/components/layout/NavBar.tsx` y `frontend/src/components/layout/Sidebar.tsx`.
- Se internacionalizaron vistas del modulo app en `frontend/src/app/app/export/page.tsx` y `frontend/src/app/app/shortDetails/page.tsx`, incluyendo etiquetas, estados y acciones.
- Se ajustaron etiquetas de sidebar en espanol para navegacion mas natural: `Editor de tiempo` y `Editor de audio`.
- Se internacionalizo `frontend/src/app/app/page.tsx` para el flujo Home (opciones de procesamiento, perfiles, mensajes de estado/upload y errores principales en es/en).
- Se internacionalizo `frontend/src/app/app/library/page.tsx` (copy principal, busquedas, estados vacios, acciones de cards y paginacion en es/en).
- Se internacionalizaron `frontend/src/app/app/timeline/page.tsx` y `frontend/src/app/app/audio_editor/page.tsx` en sus textos de UI, mensajes de estado y errores mas frecuentes.
- Se internacionalizo `frontend/src/app/app/share/[clipId]/page.tsx` (estado de conexion/publicacion YouTube, asistente IA, metadata, errores y feedback de publicacion en es/en).
- Se internacionalizaron componentes reutilizados de Home (`frontend/src/components/home/ProjectStatusPanel.tsx`, `frontend/src/components/home/GeneratedClipsSection.tsx`, `frontend/src/components/home/UploadDropzone.tsx`, `frontend/src/components/home/VideoSettings.tsx`) para evitar mezcla de idioma en el dashboard.
- Se ajusto generacion de metadata YouTube para enviar locale actual (`lang`) al backend desde `frontend/src/services/videoApi.ts`, permitiendo que el proveedor IA reciba contexto de idioma (`es`/`en`).
- Se agrego persistencia de metadata YouTube por clip+locale en `frontend/src/app/app/share/[clipId]/page.tsx` para que titulo/descripcion/hashtags/tags no se pierdan al recargar.
- Se agrego limpieza de borradores de sesion al logout en `frontend/src/store/useAuthStore.ts` (Home, Timeline, Audio editor, Share metadata y estado OAuth temporal).
- Se resolvio fallo de CI en `npm ci` sincronizando lockfile y fijando `@swc/helpers@0.5.19` en `frontend/package.json` + `frontend/package-lock.json`.

### Commits de esta rama (frontend)

- `feat(frontend): add next-intl foundation and translate landing/auth shell`
- `feat(frontend): translate export and short details app views`
- `fix(frontend): localize sidebar editor labels in spanish`
- `feat(frontend): translate app home library timeline and audio editor`
- `feat(frontend): translate share page and home reusable components`
- `fix(frontend): persist share metadata drafts and clear session artifacts on logout`
- `fix(frontend): pin swc helpers and sync lockfile for ci`
- `docs(frontend): log i18n rollout for landing auth and shell`
- `docs(frontend): update i18n worklog with app view translation batch`
- `docs(frontend): log sidebar label localization adjustment`
- `docs(frontend): log i18n translation pass for main app screens`
- `docs(frontend): log i18n sweep for share route and home components`
- `docs(frontend): log share metadata persistence and logout cleanup`
- `docs(frontend): add smoke checklist for i18n share metadata flow`
- `docs(frontend): log ci lockfile sync fix`

### Validaciones locales

- `npm run lint` -> OK
- `npm run test` -> OK
- `npm run build` -> OK

### Smoke checklist manual (i18n + metadata YouTube)

- [ ] En `/app/share/[clipId]` con locale `es`, ejecutar `Generar datos con IA` y confirmar titulo/descripcion en espanol.
- [ ] Recargar la pagina y validar que titulo/descripcion/hashtags/tags se restauran desde draft local.
- [ ] Cambiar locale a `en`, volver a ejecutar sugerencia IA y validar salida en ingles.
- [ ] Recargar nuevamente en `en` y confirmar persistencia por `clip + locale`.
- [ ] Hacer `logout` y verificar que se limpian drafts de Home/Timeline/Audio editor/Share metadata.
- [ ] Iniciar sesion otra vez y confirmar que Share abre con valores por defecto (sin draft previo).

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feat/frontend-light-latte-seo-hardening`

### Objetivo

Actualizar la landing para reflejar el alcance real actual de la app web, mostrar demos/capturas nuevas del flujo productivo y alinear el discurso a estado operativo (sin mensajes de preproduccion).

### Cambios implementados en curso

- Se refactorizo `frontend/src/app/page.tsx` para reposicionar la propuesta de valor: flujo completo `upload -> jobs -> timeline -> audio editor -> biblioteca -> exportacion -> compartir`.
- Se removieron textos de etapa temprana (ej. "Estado real", "produccion interna", "preparacion") para dejar una narrativa alineada al uso actual del producto.
- Se corrigio la tarjeta de demo 02 para que represente `Entrevista` (antes figuraba como Deportes con archivo de entrevista).
- Se ampliaron demos de landing con assets reales en `frontend/public/landing-demos/`: `video4_generando_texto_hastag_IA.mp4`, `video5_subida_audio.mp4`, `video6_añade_audio_a_video.mp4`, `home_desktop.png`, `home_movile.png`.
- Se actualizo `DemoSlot` para renderizar tanto videos como imagenes (capturas) dentro de la misma grilla responsive.
- Se removieron las capturas `home_desktop.png` y `home_movile.png` de la grilla de landing por ruido visual.
- Se separaron `Timeline` y `Audio Editor` en una seccion destacada con layout en dos columnas y reproduccion automatica (`autoplay + muted + loop`) para mostrar ambos flujos lado a lado.
- Se incorporo base de theming claro/oscuro en todo el frontend con `ThemeProvider` + toggle global persistido en `localStorage` (`hc-theme`).
- Se migraron tokens globales de `frontend/src/app/globals.css` a variables CSS para soportar Catppuccin Mocha (dark) y Latte (light) sin romper la paleta principal del producto.
- Se ajusto contraste del modo light en acciones criticas (ej. boton `Cerrar sesion`) y mensajes de error en tonos rose para mejorar legibilidad sobre fondos claros.
- Se ajusto paleta del `HaceloCortoLogo` para modo light usando variables CSS dedicadas, mejorando contraste del isotipo y gradientes en navbar/landing.
- QA final light mode: se reforzaron variantes `rose-300/rose-400` (texto/borde/fondo) y placeholders para evitar combinaciones de bajo contraste en auth, alerts y acciones destructivas.
- Se ajustaron FAQ y CTA para incluir integracion YouTube + metadata IA, audio editor y biblioteca de audios.
- Se cambio la variante `light` a paleta Catppuccin Macchiato en `frontend/src/app/globals.css`, ajustando tokens base (`night`, `neon`, texto, bordes, sombras y logo) para evaluar un look mas consistente con el resto del dashboard.
- Se limpiaron overrides globales agresivos del modo light (`text-white/*`, `bg-night-*`, placeholders y variantes rose) que estaban forzando colores fuera de la paleta y generaban contraste irregular.
- Se descarto el experimento Macchiato para light y se restauro Catppuccin Latte en `frontend/src/app/globals.css`, manteniendo el modo claro realmente claro.
- Se reforzaron overrides de contraste para light (`text-white*`, `border-white*`, `bg-white*`, placeholders y `logout-btn`) para evitar texto blanco sobre fondos claros en auth y dashboard.
- Se reforzo SEO tecnico base en `frontend/src/app/layout.tsx` con `metadataBase`, canonical, Open Graph, Twitter cards y robots global.
- Se agregaron `frontend/src/app/robots.ts` y `frontend/src/app/sitemap.ts` para exponer reglas de rastreo e indice XML.
- Se agrego control de indexacion para secciones privadas (`/app` y `/auth`) mediante `head.tsx` dedicados con `noindex,nofollow`.
- Se agrego metadata especifica de Home en `frontend/src/app/page.tsx` para alinear title/description/OG con el objetivo SEO principal de la landing.
- Se reemplazo la imagen social generica por endpoints dedicados `frontend/src/app/opengraph-image.tsx` y `frontend/src/app/twitter-image.tsx` (1200x630) para previews consistentes al compartir.

### Commits de esta rama (frontend)

- `feat(frontend): refresh landing to reflect full production workflow`
- `docs(frontend): log landing production refresh updates`
- `style(frontend): switch light theme to catppuccin macchiato and simplify overrides`
- `feat(frontend): add metadata, robots and sitemap for seo baseline`
- `docs(frontend): log macchiato light theme and seo baseline updates`
- `fix(frontend): restore latte light theme and enforce readable contrast`
- `feat(frontend): harden home seo metadata and social preview images`
- `docs(frontend): log latte light pass and seo image hardening updates`

### Validaciones locales

- `npm run lint` -> OK
- `npm run build` -> OK

## Seguimiento activo (rama actual)

Rama de trabajo actual: `feat/frontend-timeline-library-streamline`

## Objetivo de la rama

Simplificar el flujo entre Biblioteca y Timeline para evitar duplicidad de listados, sumar feedback de progreso/preview final en Timeline y dejar los ajustes del editor mas claros, limpios y alineados al look catppuccin.

Rama de trabajo: `feat/frontend-timeline-library-streamline`.

## Cambios realizados

- Se agrego en `frontend/src/app/app/timeline/page.tsx` una barra de progreso para la creacion del clip con polling por `job_id` y estados visuales (`En cola`, `Procesando`, `Completado`, `Error`).
- Se incorporo en Timeline una seccion de `Preview final` que reproduce el resultado renderizado cuando el backend expone `output_path`.
- Se elimino del Timeline la lista duplicada de videos subidos; ahora la pantalla trabaja sobre un unico `videoId` (o resuelto por `clipId`) y muestra CTA a Biblioteca cuando falta seleccion.
- Se agrego accion `Abrir Timeline` en `frontend/src/app/app/library/page.tsx` para cada video original, replicando el flujo de navegacion profunda que ya existia para clips.
- Se rediseño `frontend/src/components/home/VideoSettings.tsx` para incluir en Timeline `output_style` (`Vertical 9:16` y `Speaker split`) + `content_profile` (`auto`, `entrevista`, `deporte`, `musica`) con UI mas limpia.
- Se removieron de ajustes de timeline valores sin uso real (`crop`, `face tracking`, `color filter`, `videoStart`, `videoEnd`) y se alinio el store en `frontend/src/store/useVideoSettingsStore.ts` a parametros vigentes del backend.
- Se actualizo `frontend/src/components/home/VideoSettingsModal.tsx` para mantener consistencia de tipos/ajustes y evitar deuda tecnica por campos obsoletos.
- Se persistio la sesion de Timeline en `localStorage` (`timeline:editor-session`) para conservar video activo + job en curso/resultado al recargar o navegar, evitando que se pierda el contexto de trabajo.
- Se agrego el asset `frontend/public/landing-demos/video1_musica.mp4` para la seccion de demos de landing.
- Se simplifico `frontend/src/app/app/audio_editor/page.tsx` removiendo listado/buscador/paginacion de videos para replicar el enfoque de Timeline: editor sobre un unico `videoId`/`clipId` proveniente de Biblioteca.
- Se agrego CTA a Biblioteca en Audio Editor cuando no hay video seleccionado, evitando estado vacio confuso.
- Se incorporo en Biblioteca (videos originales) el boton `Abrir en Audio Editor` en `frontend/src/app/app/library/page.tsx`, alineando la navegacion con clips.
- Fix de compatibilidad temporal con backend en `frontend/src/app/app/audio_editor/page.tsx`: `audio_volume` ahora se envia como entero (`1` o `2`) para evitar `500` por validacion de `JobAddAudioResponse`.
- Se agrego fallback visual en previews de clips en `frontend/src/app/app/library/page.tsx` para mostrar aviso cuando el `<video>` falla al reproducir (sin dejar card vacia/negra).
- Se reemplazo el reproductor nativo de audio por un componente custom catppuccin (`frontend/src/components/audio/AudioPlayer.tsx` + `AudioPlayer.module.css`) reutilizado en `Audio editor` y `Biblioteca`.
- Ajuste UX del player custom: se removio el bloque visual superior y se reorganizo el layout en dos filas limpias (arriba progreso/tiempos, abajo volumen), con foco en simplicidad visual.

## Commits realizados

- `feat(frontend): streamline timeline flow and add job progress preview`
- `fix(frontend): persist timeline editor session across reloads`
- `chore(frontend): add landing demo video1 asset`
- `feat(frontend): streamline audio editor entry from library`
- `fix(frontend): send integer audio volume and add clip preview fallback`
- `feat(frontend): redesign custom audio player with catppuccin UI`
- `refactor(frontend): simplify audio player layout for cleaner controls`
- `docs(frontend): log timeline-library streamlining and settings cleanup`

## Archivos clave

- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/app/app/library/page.tsx`
- `frontend/src/components/home/VideoSettings.tsx`
- `frontend/src/components/home/VideoSettingsModal.tsx`
- `frontend/src/store/useVideoSettingsStore.ts`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Checklist antes de PR a develop

- [x] Rama nueva creada desde `develop`
- [x] Cambios limitados al alcance frontend/documentacion de esta iteracion
- [x] `npm run lint` OK
- [x] Documentacion actualizada

### Objetivo

Alinear el frontend con los cambios recientes de backend: dejar de usar el endpoint legacy `/auto`, exponer opciones nuevas de subtitulos/watermark, mostrar progreso real de creacion de clips y agregar soporte inicial de audios en Home + Library.

### Cambios implementados en curso

- Se actualizo `frontend/src/services/videoApi.ts` para eliminar el fallback al endpoint removido `/api/v1/jobs/reframe/{video_id}/auto`; ahora Home usa solo `POST /auto2`.
- Se ampliaron los payloads de jobs (auto y manual) para soportar `subtitles` y `watermark`, con UI de configuracion en Home y Timeline.
- Se agrego seguimiento de avance real en Home (`ProjectStatusPanel`), mostrando porcentaje y conteo de jobs listos/en proceso/error durante la generacion de clips.
- Se extendio la carga inicial para aceptar archivos de audio (`video/*,audio/*`) y se incorporaron endpoints de audios en `videoApi` (`upload`, `list`, `url`, `delete`).
- Se agrego vista de `Audios` en `frontend/src/app/app/library/page.tsx` con busqueda, preview bajo demanda y eliminacion.
- Se ajustaron mensajes de estado para diferenciar uploads de video/audio sin romper la experiencia de clips.
- Hotfix: se restauro normalizacion de `output_path` (cuando backend responde JSON) en `frontend/src/services/videoApi.ts` para evitar previews rotos con `src="[object Object]"`.
- Se agrego en `frontend/src/app/app/timeline/page.tsx` el flujo de mezcla de audio sobre video: seleccion de audio, preview, parametros (`offset`, `start/end`, `volume`) y envio de job a `POST /api/v1/jobs/add-audio/{video_id}`.
- Se incorporo polling de estado para jobs de mezcla de audio en Timeline y preview del output final cuando el backend devuelve `output_path`.
- Se reforzo la visualizacion de avance en `frontend/src/components/home/ProjectStatusPanel.tsx` con barra segmentada por estados (listo/error/pendiente) y colores diferenciados.
- Se rediseño la card de audio en `frontend/src/app/app/library/page.tsx` para que tenga look catppuccin (gradientes violeta/rosa, onda visual y reproductor de preview mas integrado al estilo actual).
- Se integro `POST /api/v1/videos/from-job/{job_id}` en `frontend/src/app/app/library/page.tsx` para importar clips como videos reeditables desde la biblioteca.
- Se movio el flujo de mezcla a una nueva ruta dedicada `frontend/src/app/app/audio_editor/page.tsx` (selector de video + audio, parametros y visual de pistas), y Timeline ahora solo enlaza al nuevo editor.
- Se agrego acceso directo desde biblioteca de clips a `Audio editor` con query params (`videoId`, `clipId`) para abrir el video correcto.
- Fix UX: se acotaron pistas y campos del `Audio editor` a la duracion real del video/audio para evitar que el track se desborde visualmente o exceda el largo maximo permitido.
- Ajuste de biblioteca: se removio `Importar a Videos` en cards de clips y se priorizo navegacion directa a `Timeline` + `Audio editor`.
- Se integro flujo real de YouTube en `frontend/src/app/app/share/[clipId]/page.tsx`: estado de conexion, CTA de conexion OAuth Google y publicacion real por `POST /api/v1/youtube/publish/{job_id}`.
- Se agregaron en `frontend/src/services/videoApi.ts` los contratos para `GET /api/v1/youtube/status` y `POST /api/v1/youtube/publish/{job_id}`.
- Hotfix share: se cambio la carga del clip a `GET /api/v1/jobs/{job_id}` (en lugar de busqueda por listado) y se agrego mensaje/reintento explicito para errores de red (`Failed to fetch`).
- Se agrego asset de demo para landing en `frontend/public/landing-demos/video2_entrevista.mp4` para habilitar preview real en Home (`/landing-demos/video2_entrevista.mp4`).

### Commits de esta rama (frontend)

- `feat(frontend): sync auto2 flow, clip progress and audio library support`
- `docs(frontend): log auto2 and audio frontend refresh`
- `feat(frontend): add timeline audio-mix workflow and segmented clip progress`
- `feat(frontend): add import-from-job action in clips library`
- `feat(frontend): move audio workflow into dedicated audio editor route`
- `feat(frontend): connect share screen to real youtube publish endpoints`

### Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run build` -> OK
- `npm run test -- --run` -> OK

## Objetivo de la rama

Retirar de la vista de estado del proyecto las acciones de descarga (obtener URL y descargar video) para reutilizarlas despues en otra pantalla, manteniendo la UI actual limpia y enfocada.

Rama de trabajo: `feat/frontend-extract-download-actions`.

## Cambios realizados

- Se extrajeron los botones de `Obtener URL de descarga` y `Descargar video subido` desde `frontend/src/components/home/ProjectStatusPanel.tsx` para que ya no se muestren en la seccion de estado del proyecto.
- Se creo el componente reutilizable `frontend/src/components/home/DownloadVideoActions.tsx` con la logica de resolucion de URL y accion de descarga para uso futuro en otra vista.
- Se simplifico `frontend/src/app/app/page.tsx` removiendo estado y props de descarga que ya no corresponden a esta pantalla (`downloadData`, `downloadError`, `isResolvingDownloadUrl`, `handleResolveDownloadUrl`).
- Se mantuvo el flujo de upload y preview sin cambios visuales fuera del panel de estado.

## Commits realizados

- `feat(frontend): move download actions out of project status panel`
- `docs(frontend): update PR log for download actions extraction`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/components/home/ProjectStatusPanel.tsx`
- `frontend/src/components/home/DownloadVideoActions.tsx`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] Documentacion actualizada

## Objetivo de la rama

Integrar sobre `develop` actualizado el flujo completo de timeline + biblioteca (frontend/backend) para dejar operativas las vistas de clips/videos, acciones CRUD, navegacion de edicion profunda y ruta de compartir.

Rama de trabajo: `feature/integracion-timeline-library-flow`.

## Cambios realizados

- Se integraron en `frontend/src/app/app/page.tsx` y `frontend/src/components/home/GeneratedClipsSection.tsx` las mejoras de Home para jobs automaticos, persistencia de draft, polling estable y transiciones de preview.
- Se incorporo `frontend/src/app/app/timeline/page.tsx` con editor manual conectado al endpoint de reframe, incluyendo seleccion de clip/video, paginacion y busqueda contra backend.
- Se amplió `frontend/src/app/app/library/page.tsx` con vistas de `Clips` y `Videos originales`, mas acciones de renombrar/eliminar para videos y editar/compartir/eliminar para clips.
- Se agrego `frontend/src/app/app/share/[clipId]/page.tsx` para preparar el flujo de compartir por red social y se fortalecio el deep-link de `Editar` hacia timeline por `clipId`/`videoId`.
- Se actualizaron servicios en `frontend/src/services/videoApi.ts` para soportar listados paginados/buscables, CRUD de videos y clips, y creacion de jobs manuales/automaticos.
- Se aplico refresh visual en dashboard (`frontend/src/app/globals.css`, `frontend/src/components/branding/HaceloCortoLogo.tsx`, `frontend/src/components/layout/NavBar.tsx`) con paleta Catppuccin y correccion de navegacion del logo.

## Commits realizados

- `feat(frontend): wire home upload flow to auto reframe jobs endpoint`
- `feat(frontend): move preview workflow to timeline and fetch user clips`
- `feat(frontend): add backend search and original videos library view`
- `feat(frontend): wire timeline editor to manual reframe endpoint`
- `feat(frontend): add rename and delete actions to library videos`
- `feat(frontend): add clip share route and stronger timeline edit deep-link`
- `style(frontend): switch dashboard palette to catppuccin and fix home logo link`

## Archivos clave

- `frontend/src/app/app/page.tsx`
- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/app/app/library/page.tsx`
- `frontend/src/app/app/share/[clipId]/page.tsx`
- `frontend/src/services/videoApi.ts`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop` actualizado
- [x] Integracion de cambios frontend/backend de `feature/frontend-backend-timeline-library-flow`
- [x] `npm run lint` OK
- [x] Documentacion actualizada

## Objetivo de la rama

Ajustar el frontend a cambios recientes de backend en `develop`, priorizando estabilidad del flujo de timeline (crear clips y guardar nombre de video).

Rama de trabajo: `feature/frontend-sync-upload-develop`.

## Cambios realizados

- Se alineo el timeline con la validacion actual de backend (duracion minima de 5s por clip) en `frontend/src/app/app/timeline/page.tsx` y `frontend/src/components/home/videoPrevewTimeLine/useVideoTrim.ts`.
- Se reforzo el panel de ajustes en `frontend/src/components/home/VideoSettings.tsx` mostrando duracion estimada, minimo permitido y bloqueo del boton cuando el recorte no cumple reglas.
- Se corrigio guardado de nombre en timeline para usar el `selectedVideoId` real y refrescar listado local luego de editar filename.
- Se corrigio manejo de error en guardado de nombre para mostrar el mensaje real del backend en lugar de estado previo.
- Se eliminaron warnings de lint pendientes en timeline/settings para mantener baseline limpia.
- Se adapto la integracion de Home para el refactor de backend priorizando `POST /api/v1/jobs/reframe/{video_id}/auto2` con fallback automatico a `/auto` cuando `auto2` no existe.
- Se normalizo la respuesta de `auto2` en frontend para no romper el flujo aunque no devuelva arreglo `jobs`.
- Se agrego polling temporal de biblioteca tras generar jobs automaticos para hidratar clips cuando el backend procesa de forma asincronica y no retorna jobs individuales de inmediato.
- Se envio `clips_count` y `clip_duration_sec` por defecto desde frontend al crear jobs automaticos para evitar `400` en `auto2` cuando backend exige esos parametros.
- Se mejoro el mensaje de error en Home para mostrar detalle real de backend (ya no se tapa siempre con mensaje generico de archivo invalido).
- Se ajusto Home para que la hidratacion de clips siga activa hasta completar la cantidad esperada de resultados, evitando que aparezca solo el primer clip si el resto termina mas tarde.
- Se mejoro la grilla de `clips generados` en Home para que una sola tarjeta no se estire a pantalla completa (cards con ancho consistente desde el primer render).
- Se removio la opcion lateral `Settings IA` del sidebar.
- Se creo `frontend/src/app/app/export/page.tsx` como nueva vista de exportacion con resumen de estado, listado de clips listos, descarga directa y copia de link.
- Se corrigio Home para que la lista de resultados combine `createdJobs` con clips ya visibles en biblioteca del mismo `video_id`, evitando que se muestre solo 1 clip hasta recargar cuando los 3 jobs llegan de forma asincronica.

## Nota destacada

- Dependencia backend detectada fuera del alcance de este PR frontend: si el worker usa un volumen/path sin permisos de escritura para temporales, el pipeline puede fallar con `PermissionError` y dejar jobs sin completar.
- Seguimiento recomendado para PR backend: parametrizar y validar el path temporal por entorno (ej. `WORKER_OUTPUT_DIR`) y verificar permisos del volumen en deploy.

## Commits realizados

- `fix(frontend): align timeline clip creation with backend constraints`
- `fix(frontend): support auto2 job orchestration and async clip hydration`
- `fix(frontend): send auto2 defaults and surface backend 400 details`
- `docs(frontend): log timeline compatibility updates on develop sync`
- `docs(frontend): update worklog with auto2 integration fixes`
- `docs(frontend): record upload and worker stability fixes`
- `feat(frontend): polish home clips grid and add export center view`
- `docs(frontend): update worklog with home hydration and export page`
- `fix(frontend): sync home clips with library hydration fallback`
- `docs(frontend): log home clip sync fix without manual refresh`

## Archivos clave

- `frontend/src/app/app/timeline/page.tsx`
- `frontend/src/components/home/VideoSettings.tsx`
- `frontend/src/components/home/videoPrevewTimeLine/useVideoTrim.ts`
- `frontend/src/components/home/GeneratedClipsSection.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/app/app/export/page.tsx`
- `frontend/src/app/app/page.tsx`
- `docs/frontend-pr-log.md`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
- `npm run test -- --run` -> OK
- `npm run build` -> OK

## Checklist antes de PR a develop

- [x] Rama creada desde `develop`
- [x] Commits convencionales y atomicos
- [x] `npm run lint` OK
- [x] `npm run test` OK
- [x] `npm run build` OK
- [x] Documentacion actualizada

## Objetivo de la rama

Actualizar la landing para reflejar el estado real del MVP actual y dejar preparada una seccion de demos con videos propios del equipo.

Rama de trabajo: `feature/frontend-landing-mvp-sync`.

## Cambios implementados

- Se actualizo la landing en `frontend/src/app/page.tsx` con contenido alineado al flujo vigente (`/app`, `/app/timeline`, `/app/library`, `/app/export`).
- Se ajustaron textos/FAQ para evitar promesas fuera del alcance actual y mostrar estado real del producto.
- Se agrego seccion de demos en landing con reproductores preparados para archivos estaticos.
- Se creo carpeta de assets `frontend/public/landing-demos/` con `.gitkeep` para versionar estructura.
- Nombres esperados para demos:
  - `video1_musica.mp4`
  - `video2_entrevista.mp4`
  - `video3_timeline.mp4`

## Validaciones locales

Ejecutado en `frontend/`:

- `npm run lint` -> OK
