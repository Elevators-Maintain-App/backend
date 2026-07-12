# Tablero de trabajo

> Última actualización: 12 de julio de 2026.
>
> El tablero fue reconciliado con `main` en el commit `a8ed5b5`. Cada tarea debe aparecer en un solo estado.

## Ready

### `DEVOPS-001` — Incorporar pruebas antes del despliegue backend

Objetivo:

* agregar un job de pruebas aisladas;
* impedir el build y deploy cuando las pruebas fallen;
* evaluar activación del workflow en pull requests.

Dependencia:

* confirmar primero que la suite completa pasa en el entorno local aislado.

Prioridad: crítica.

### `DOC-001` — Actualizar el README principal

Objetivo:

* reemplazar la descripción genérica;
* documentar backend y frontend web;
* corregir comandos de pruebas y migraciones;
* explicar despliegues independientes.

Prioridad: media.

### `DOC-002` — Reconciliar documentación de planes

Objetivo:

* marcar slices ya implementados;
* separar decisiones vigentes de instrucciones históricas;
* evitar que Codex trate trabajo terminado como pendiente.

Prioridad: media.

### `WEB-001` — Validar configuración de lint

Objetivo:

* ejecutar `npm run lint`;
* confirmar compatibilidad de `next lint`;
* corregir el script solamente si falla por incompatibilidad real.

Prioridad: media.

## In Progress

Ninguna tarea confirmada.

## Review

### `DOC-AI-001` — Configuración del flujo asistido por IA

Alcance:

* actualización de `AGENTS.md`;
* creación del índice de documentación;
* creación de estado, backlog y tablero;
* configuración separada del proyecto en ChatGPT.

Estado:

* contenido preparado;
* pendiente revisión final del desarrollador;
* pendiente `git diff --check`;
* pendiente commit en una rama documental.

## Validation

### `PLAN-001` — Validar estado final de planes y suscripciones

Implementación confirmada:

* backend;
* endpoints;
* enforcement;
* pruebas específicas;
* primera versión web.

Pendiente:

* ejecutar suite backend completa;
* ejecutar typecheck, lint y build web;
* reconciliar roadmap y documentación histórica;
* realizar validación manual de los flujos principales.

## Blocked

### `DB-001` — Baseline Alembic reproducible

Bloqueo:

* requiere estudiar el historial de bases existentes;
* debe evitar alterar revisiones ya aplicadas;
* necesita plan de transición y rollback.

No debe incluirse incidentalmente en otra funcionalidad.

### `SEC-001` — Proteger endpoints públicos legacy

Bloqueo:

* requiere revisar consumidores mobile y web;
* algunos endpoints necesitan reemplazos protegidos antes de retirar acceso público;
* debe dividirse por dominio y riesgo.

No debe resolverse mediante un cambio masivo.

## Done

### `OT-ITER2-001` — Iteración backend de horas extra, Slices 1–6

Completado:

* integridad autoritativa contra solapamientos y restricción GiST concurrente;
* edición parcial, recálculo, cancelación lógica, auditoría y locks;
* listados `/page`, filtros y paginación sin romper los arrays legacy;
* exportaciones PDF y XLSX con límites y protección contra fórmulas;
* migraciones `c4f8a1d2e6b9` y `e7a3c9d4f2b1`;
* auditoría final del Slice 6 y handoff contractual mobile;
* suite final: `359 passed`, `36 warnings`, `0 failed`;
* integración en `main` mediante `bf6fc5f`, sincronizada con `origin/main`;
* despliegue en GCP y migraciones de producción completados según evidencia del desarrollador;
* producción reportada en `e7a3c9d4f2b1 (head)`.

La adopción y validación React Native continúan exclusivamente en el repositorio mobile. Los defectos
backend que allí aparezcan serán correcciones puntuales, no slices backend conocidos pendientes.

### Aislamiento de base de datos de pruebas

Completado:

* `docker-compose.test.yml`;
* PostgreSQL efímero `db-test`;
* validación de entorno y URL;
* guardas contra bases remotas;
* bootstrap controlado mediante `create_all + stamp`;
* documentación de uso seguro.

### Backend de horas extra — primera iteración

Completado en código:

* modelo y migración;
* cálculo;
* servicios;
* API;
* flujo de aprobación;
* pruebas específicas;
* documentación de arquitectura.

La validación completa y la segunda iteración quedaron cerradas en `OT-ITER2-001`.

### Base de planes y suscripciones

Completado en código:

* persistencia;
* servicios;
* límites y enforcement;
* endpoints;
* seeds;
* pruebas específicas;
* primera versión web.

La validación completa y reconciliación documental permanecen en `PLAN-001` y `DOC-002`.

## Regla de movimiento

Una tarea avanza de esta forma:

```text
Ready → In Progress → Review → Validation → Done
```

Usar `Blocked` cuando exista una dependencia concreta que impida avanzar.

Al cerrar cada sesión:

1. mover cada tarea al estado real;
2. actualizar `docs/project-status.md`;
3. registrar pruebas y comandos ejecutados;
4. indicar el siguiente punto exacto;
5. no mover una tarea a `Done` si falta validación obligatoria.
