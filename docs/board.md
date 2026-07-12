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

### `OT-ITER2-001` — Iteración backend de horas extra, Slices 1–6

Evidencia en `db-test`:

* Slice 1 preservado con restricción `excl_overtime_requests_active_overlap`;
* Slice 2 agrega PATCH parcial, cancelación trazable y locks de fila;
* Alembic `heads/current`: `e7a3c9d4f2b1 (head)`;
* downgrade bloqueado ante auditoría nueva y ciclo limpio downgrade/upgrade: OK;
* focalizadas: `62 passed`, `34 warnings`;
* módulo: `94 passed`, `34 warnings`;
* suite completa: `329 passed`, `36 warnings`;
* cinco pruebas PostgreSQL de integridad/concurrencia: OK.
* Slice 3 agrega `/page` para técnico/supervisor sin modificar arrays legacy;
* rango Panamá, máximo 366 días, conteo SQL y orden estable validados;
* focalizadas Slice 3: `70 passed`, `34 warnings`;
* módulo acumulado: `108 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`;
* suite completa acumulada: `343 passed`, `36 warnings`.
* Slice 4 agrega PDF binario directo para supervisor, sin paginación accidental;
* límite de 2000, totales por técnico/general y resultado vacío validados;
* renderer real WeasyPrint: `2 passed`, `30 warnings`;
* focalizadas acumuladas: `78 passed`, `34 warnings`;
* módulo acumulado: `116 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`;
* suite completa acumulada: `351 passed`, `36 warnings`.
* Slice 5 agrega XLSX binario directo con tres hojas y tipos Excel nativos;
* límite XLSX de 10000 previo a carga/render, defensa de fórmulas y PDF preservado;
* dependencia directa reproducible `openpyxl>=3.1.2`;
* renderer XLSX: `3 passed`, `30 warnings`;
* focalizadas acumuladas: `83 passed`, `34 warnings`;
* módulo acumulado: `123 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`.
* suite completa acumulada: `358 passed`, `36 warnings`, `0 failed`.
* Slice 6 audita el diff, elimina carga de eventos en `/page` y alinea OpenAPI binario;
* OpenAPI confirma 15 operaciones, PATCH, precedencia y `format=pdf|xlsx`;
* ciclo limpio `e7a3c9d4f2b1 → c4f8a1d2e6b9 → e7a3c9d4f2b1`: OK en `db-test`;
* focalizadas finales por capa: `113 passed`, `34 warnings`;
* módulo overtime final: `124 passed`, `34 warnings`;
* suite completa final: `359 passed`, `36 warnings`, `0 failed`;
* handoff React Native creado en `docs/overtime-mobile-handoff-iteration-2.md`.

Pendiente para `Done`: implementación mobile y validación manual integrada tras despliegue coordinado.

### `OT-001` — Validar backend de horas extra integrado en `main`

Implementación confirmada:

* persistencia y cálculo;
* flujo de aprobación;
* endpoints;
* pruebas específicas;
* documentación de arquitectura.

Pendiente:

* ejecutar suite backend completa después del merge;
* confirmar migración actual en `db-test`;
* confirmar despliegue backend;
* contrastar contrato con el repositorio mobile.

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

### Aislamiento de base de datos de pruebas

Completado:

* `docker-compose.test.yml`;
* PostgreSQL efímero `db-test`;
* validación de entorno y URL;
* guardas contra bases remotas;
* bootstrap controlado mediante `create_all + stamp`;
* documentación de uso seguro.

### Backend de horas extra

Completado en código:

* modelo y migración;
* cálculo;
* servicios;
* API;
* flujo de aprobación;
* pruebas específicas;
* documentación de arquitectura.

La validación completa permanece en `OT-001`.

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
