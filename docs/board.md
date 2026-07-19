# Tablero de trabajo

> Última actualización: 16 de julio de 2026.
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

### `WEB-002` — Carga administrativa de plantillas de checklist JSON

Implementado en `feature/web-admin-checklist-upload`:

* página protegida `/dashboard/admin/checklists` y navegación exclusiva de `admin` en escritorio y móvil;
* listado global protegido `GET /api/checklists/templates`, con nombres opcionales de catálogos, pasos expandibles y estados loading/vacío/error;
* lectura local, validación Zod, vista previa responsive de pasos, detección previa de combinación ocupada y confirmación explícita de carga;
* creación y listado a través de servicio, query/mutación sin retry y allowlist de ruta exacta;
* focalizadas checklist `5 passed`, regresión mobile checklist `14 passed`, typecheck, lint y build de `apps/web`: OK;
* suite completa backend posterior: `378 passed`, `38 warnings`; integración overtime estabilizada con reloj determinista inyectado.

Pendiente:

* validación manual autenticada de listado, creación `201`, conflicto `409`, rechazo `422`, permisos y responsive.

### `OT-COMPAT-001` — Catálogo compatible de técnicos para filtros overtime

Implementado en rama `fix/overtime-supervisor-technician-catalog`:

* endpoint protegido `GET /api/overtime/supervisor/catalogs/technicians`;
* UUID PostgreSQL compatible con listado y exportaciones;
* aislamiento por compañía, rol técnico y estado activo;
* focalizadas `95 passed`, módulo `125 passed`, integración PostgreSQL `7 passed`;
* suite completa `367 passed`, `36 warnings`, `0 failed`;
* pendiente validación posterior a un despliegue autorizado desde React Native.

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

### `ORDEN-DELETE-001` — Corregir eliminación de órdenes con eventos PDF

Completado localmente:

* migración reversible `f8d2a4c6e1b0` desde `e7a3c9d4f2b1`, con un único head y `ON DELETE CASCADE` en `pdf_report_generation_events.checklist_id`;
* modelo alineado con relación ORM pasiva, endpoint DELETE sin borrados manuales y conflicto de integridad controlado como `409`;
* cobertura de eliminación con y sin eventos, aislamiento de compañía, rechazo por rol e inspección de la FK;
* downgrade inspeccionado sin política `ON DELETE` y upgrade inspeccionado con `CASCADE` en `db-test`;
* focalizadas: `13 passed`, `32 warnings`. Suite completa posterior: `378 passed`, `38 warnings`; la integración de horas extra quedó determinista mediante reloj inyectado.

Pendiente externo: validación mobile tras un despliegue autorizado.

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
