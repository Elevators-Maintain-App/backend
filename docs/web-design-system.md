# VertiOne Web Design System

VertiOne Web debe sentirse como una consola profesional para operacion tecnica: moderna, minimalista, precisa y tecnologica. La referencia visual publica es la landing `https://verti-one.com/`, que posiciona a VertiOne como una plataforma de gestion de mantenimiento tecnico.

## Principios

- Claridad operativa primero: interfaces densas, escaneables y sin decoracion innecesaria.
- Tecnologia sobria: verdes tecnicos, neutros frios, acentos calidos muy medidos.
- Consistencia por composicion: pantallas armadas con componentes reutilizables, no estilos ad hoc.
- Accesibilidad: contraste suficiente, labels visibles, foco claro y mensajes accionables.
- Modularidad: componentes base sin logica de negocio ni llamadas HTTP.

## Tokens Base

Los tokens viven en `apps/web/src/app/globals.css` y se exponen a Tailwind desde `apps/web/tailwind.config.ts`.

### Color

- `background`: fondo general frio y claro para superficies operativas.
- `foreground`: texto principal azul grafito.
- `primary`: verde VertiOne para acciones principales, foco y elementos activos.
- `secondary`: azul grafito profundo para navegacion, shells y acciones secundarias fuertes.
- `accent`: amarillo tecnico para llamados de atencion puntuales, nunca como color dominante.
- `muted`: fondos neutros para bloques secundarios, empty states y barras suaves.
- `border` / `input`: lineas frias y discretas para separar informacion.
- `destructive`: errores, eliminaciones y estados bloqueantes.
- `success`: completado, activo, validado.
- `warning`: pendiente, requiere atencion.
- `info`: informacion, sincronizacion o estados neutrales activos.

### Tipografia

- Usar la fuente del stack de Next/system por defecto hasta definir una fuente de marca.
- Page titles: `text-3xl font-semibold`.
- Section titles: `text-base font-semibold`.
- Body: `text-sm` o `text-base` segun densidad.
- Helper/error text: `text-sm`.
- No usar letter-spacing negativo.

### Radios

- Radio base: `0.5rem`.
- Cards y controles: `rounded-lg` o `rounded-md`.
- Evitar componentes excesivamente redondeados; la app debe sentirse tecnica, no juguetona.

### Sombras

- Usar sombras suaves solo para jerarquia real.
- Token disponible: `shadow-soft`.
- Cards internas y controles pueden usar `shadow-sm`.
- Evitar sombras decorativas grandes.

### Espaciado

- Layout page: `px-6 py-8` con contenedor `max-w-6xl`.
- Secciones: `gap-6`.
- Grids de metricas/cards: `gap-4`.
- Card padding: `p-5`.
- Form fields: `space-y-2` y formularios `space-y-5`.

## Estructura de Componentes

- `src/components/ui`: primitivas visuales y wrappers atomicos.
- `src/components/forms`: controles de formulario con label, hint y error.
- `src/components/layout`: shell, headers y composicion de pagina.
- `src/components/data-display`: tablas, listas, metricas y visualizaciones de datos.
- `src/components/feedback`: badges, loading, empty, error y mensajes de estado.

## Componentes Base

### AppButton

Usar para acciones principales y secundarias. Variantes permitidas vienen de `Button`: `default`, `outline`, `secondary`, `ghost`, `destructive`, `link`.

Reglas:

- Una accion primaria por region visual.
- Icono lucide cuando mejore reconocimiento.
- Texto corto, accionable y consistente.
- Deshabilitado solo cuando exista razon clara.

### AppInput

Usar para inputs de texto, email, password y busqueda simple.

Reglas:

- Label visible.
- Error debajo del campo.
- Hint opcional para restricciones no obvias.
- No mezclar transformaciones de dominio dentro del componente.

### Select

Pendiente de implementar como componente base cuando exista el primer uso real.

Reglas:

- Usar para conjuntos cerrados.
- Placeholder descriptivo.
- Estados disabled/loading claros.
- Opciones ordenadas de forma util para la tarea.

### Textarea

Pendiente de implementar como componente base cuando exista el primer uso real.

Reglas:

- Usar para notas, observaciones y explicaciones.
- Altura minima estable.
- Contador solo si hay limite real de backend.

### AppCard

Usar para agrupar unidades repetibles de informacion, metricas o paneles pequenos.

Reglas:

- No anidar cards dentro de cards.
- Header, content y description deben mantener jerarquia compacta.
- Evitar convertir secciones completas de pagina en cards decorativas.

### PageHeader

Usar al inicio de vistas funcionales.

Reglas:

- `eyebrow` identifica el modulo.
- `title` nombra la vista.
- `description` explica el alcance operativo, no instrucciones largas.
- `actions` contiene comandos principales de la vista.

### DataTable

Pendiente de implementar cuando exista un listado real.

Reglas:

- Headers estables y escaneables.
- Sorting/filtering solo cuando el caso lo necesite.
- Empty, loading y error states integrados.
- Acciones por fila con iconos y tooltips si son compactas.

### EmptyState

Pendiente de implementar en `feedback`.

Reglas:

- Mensaje breve.
- Accion primaria solo si resuelve el estado.
- No usar ilustraciones genericas.

### StatusBadge

Usar para estados cortos y discretos.

Tonos:

- `neutral`
- `success`
- `warning`
- `info`
- `danger`

### LoadingState

Pendiente de implementar en `feedback`.

Reglas:

- Skeleton para tablas/cards cuando haya estructura conocida.
- Spinner para transiciones cortas.
- No bloquear toda la pantalla salvo auth o permisos.

### ErrorState

Pendiente de implementar en `feedback`.

Reglas:

- Mensaje accionable.
- Mostrar retry cuando aplique.
- No ocultar errores de permisos o configuracion como errores genericos.
