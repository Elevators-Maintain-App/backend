# Estado actual del proyecto

> Última actualización: 18 de julio de 2026.
>
> Este documento debe actualizarse al cerrar cada sesión relevante. Debe reflejar únicamente estados comprobados mediante Git, código, migraciones, pruebas o validación manual.

## Resumen

VertiOne está compuesto por:

* una API FastAPI ubicada en `app/`;
* un frontend web Next.js ubicado en `apps/web/`;
* una aplicación mobile React Native mantenida en un repositorio independiente.

El backend se despliega en Google Cloud Run. El frontend web se configura y despliega de forma independiente en Vercel. La aplicación mobile consume los contratos protegidos de la API.

## Estado Git validado

* Rama base: `main`.
* Commit actual: `bf6fc5f` (`feat(overtime): complete backend second iteration`).
* `main` local sincronizada con `origin/main`.
* No se identificaron commits remotos pendientes al momento de la revisión.
* Working tree limpio antes de esta actualización documental.

## Estado del backend

* FastAPI con arquitectura organizada mediante rutas, servicios, repositorios, modelos y schemas.
* SQLAlchemy async con PostgreSQL.
* Migraciones administradas mediante Alembic.
* Autenticación con Firebase.
* Autorización basada en roles y compañía.
* Base de datos aislada para pruebas mediante `docker-compose.test.yml`.
* Guardas automáticas que impiden ejecutar pytest contra una base no autorizada.
* Generación de reportes mediante Jinja2 y WeasyPrint.
* Contratos compartidos con frontend web y aplicación mobile.

### Migraciones

Las migraciones recientes incluyen:

* planes, suscripciones y uso;
* eventos de generación de reportes PDF;
* solicitudes de horas extra;
* corrección de referencias de clientes con UUID.

La cabeza efectiva del grafo debe confirmarse mediante:

```bash
docker compose -f docker-compose.test.yml exec -T api-test alembic heads
```

La cadena histórica de migraciones todavía no permite reconstruir de forma confiable una base completamente vacía. En pruebas se utiliza temporalmente `create_all + stamp`, exclusivamente dentro de la base efímera `db-test`.

### Corrección de eliminación de órdenes con eventos PDF

La corrección `ORDEN-DELETE-001` queda preparada para integración local:

* migración `f8d2a4c6e1b0` sobre `e7a3c9d4f2b1` establece `ON DELETE CASCADE` en `pdf_report_generation_events.checklist_id`;
* el modelo mantiene una relación pasiva `Checklist → PdfReportGenerationEvent`, para que PostgreSQL sea la autoridad de la cascada;
* `DELETE /api/ordenes-trabajo/{orden_id}` conserva contrato `204` y permisos; convierte integridad residual en `409` después de rollback;
* se validaron eliminación con eventos y sin eventos, aislamiento de compañía y denegación al técnico;
* el downgrade restaura la FK previa sin acción `ON DELETE` y el upgrade vuelve a `CASCADE`; la única cabeza local es `f8d2a4c6e1b0`.

Revisión de FKs hijas: `ChecklistItem` y `OrdenTrabajoSeguimiento` se eliminan mediante las relaciones ORM ya existentes de checklist/orden; `EvidenciaMultimedia` también depende de la cascada ORM de orden. `PdfReportGenerationEvent.orden_id` permanece restrictiva para eventos sin `checklist_id`; esos casos no forman parte de esta corrección y reciben el `409` controlado del DELETE.

## Estado del frontend web

* Next.js App Router en `apps/web`.
* React 19 y TypeScript.
* Autenticación mediante Firebase Auth.
* Guards y navegación por roles.
* React Query para estado del servidor.
* Axios mediante cliente API centralizado.
* Formularios con Zod y React Hook Form.
* Design system inicial basado en Tailwind y componentes compatibles con shadcn/ui.
* Áreas observadas:

  * autenticación;
  * dashboards por rol;
  * portal de cliente;
  * administración de usuarios;
  * planes y suscripciones.

Los endpoints web deben usar `/api/web/*` por defecto o endpoints core protegidos y documentados.

## Funcionalidades recientes confirmadas

### Solicitudes de horas extra

Corrección contractual `OT-COMPAT-001` implementada en la rama
`fix/overtime-supervisor-technician-catalog`: se agregó el catálogo supervisor de técnicos activos
con UUID PostgreSQL para uso directo en filtros paginados y exportaciones. No modifica el LOV legacy
ni requiere migración. Validación de la rama: focalizadas `95 passed`, módulo overtime `125 passed`,
integración PostgreSQL `7 passed`, regresión PDF/XLSX `5 passed` y suite completa `367 passed`,
`36 warnings`, `0 failed`. Falta la validación mobile posterior a un despliegue autorizado.

La implementación backend fue integrada en `main` mediante:

* `6cae4c2` — persistencia y fundamentos de cálculo;
* `ef73f68` — API y flujo de aprobación;
* `42449f6` — integración de la rama de horas extra.

Componentes observados:

* modelo y migración;
* schemas;
* servicio de solicitudes;
* calculadora de horas;
* endpoints;
* autorización y visibilidad por roles;
* pruebas unitarias, de repositorio y de API;
* documentación de arquitectura.

Estado actual:

* backend integrado en `main`;
* primera iteración desplegada y validada históricamente con `300 passed`, `36 warnings`, `0 failed`;
* frontend mobile mantenido, desarrollado y validado en su repositorio independiente.

Segunda iteración backend, Slices 1–6, integrada en `main` mediante `bf6fc5f`:

* validación previa de jornadas activas solapadas con `409` estable;
* garantía PostgreSQL mediante restricción GiST parcial por compañía, técnico y rango semiabierto;
* migración nueva que falla explícitamente ante datos preexistentes incompatibles;
* pruebas unitarias, API e integración/concurrencia añadidas;
* Alembic confirmado en `c4f8a1d2e6b9 (head)` y ciclo downgrade/upgrade validado en `db-test`;
* pruebas focalizadas: `40 passed`, `34 warnings`;
* módulo de horas extra: `72 passed`, `34 warnings`;
* suite backend completa: `307 passed`, `36 warnings`, `0 failed`;
* validación manual del flujo HTTP permanece pendiente.
* edición parcial propia de solicitudes `pending`, con combinación omitido/`null`, revalidación y recálculo;
* cancelación lógica `pending → cancelled`, eventos `edited`/`cancelled` y locks contra revisiones concurrentes;
* migración `e7a3c9d4f2b1` sobre `c4f8a1d2e6b9`, con downgrade seguro y cabeza confirmada;
* focalizadas acumuladas: `62 passed`, `34 warnings`;
* módulo acumulado: `94 passed`, `34 warnings`;
* suite backend acumulada: `329 passed`, `36 warnings`, `0 failed`;
* cinco pruebas PostgreSQL de solapamiento, liberación de franja y carreras: OK;
* validación integrada con React Native corresponde al repositorio mobile.
* listados `/page` para técnico y supervisor con conteo SQL, rango efectivo y orden determinista;
* endpoints array legacy preservados sin cambios de parámetros ni respuesta;
* rango default de 31 fechas en Panamá y máximo inclusivo de 366 días;
* Slice 3 sin migración; cabeza Alembic preservada en `e7a3c9d4f2b1`;
* focalizadas Slice 3: `70 passed`, `34 warnings`;
* módulo acumulado: `108 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`;
* suite backend acumulada: `343 passed`, `36 warnings`, `0 failed`.
* exportación PDF binaria para supervisor con filtros compartidos y límite de 2000;
* renderer local Jinja2/WeasyPrint, autoescape, totales por técnico y total general;
* resultado vacío y duraciones mayores de 24 horas soportados;
* Slice 4 sin migración ni dependencia nueva; Alembic permanece en `e7a3c9d4f2b1`;
* renderer PDF: `2 passed`, `30 warnings`;
* focalizadas acumuladas: `78 passed`, `34 warnings`;
* módulo acumulado: `116 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`;
* suite backend acumulada: `351 passed`, `36 warnings`, `0 failed`.
* exportación XLSX binaria con detalle, resumen por técnico y resumen general;
* fechas/horarios nativos, duraciones `[h]:mm`, textos protegidos contra fórmulas y totales sin fórmulas;
* límite XLSX de 10000 antes de cargar filas; PDF conserva límite y contrato de Slice 4;
* dependencia directa `openpyxl>=3.1.2`; Slice 5 sin migración y Alembic en `e7a3c9d4f2b1`;
* renderer XLSX: `3 passed`, `30 warnings`;
* focalizadas acumuladas: `83 passed`, `34 warnings`;
* módulo acumulado: `123 passed`, `34 warnings`;
* integración PostgreSQL acumulada: `6 passed`, `30 warnings`.
* suite backend acumulada: `358 passed`, `36 warnings`, `0 failed`.
* Slice 6 completó auditoría integral, contrato OpenAPI binario y optimización de `/page` sin eventos;
* migraciones acumuladas verificadas con ciclo limpio y constraint/enums inspeccionados en `db-test`;
* focalizadas finales por capa: `113 passed`, `34 warnings`;
* módulo overtime final: `124 passed`, `34 warnings`;
* suite backend final: `359 passed`, `36 warnings`, `0 failed`;
* handoff mobile autocontenido: `docs/overtime-mobile-handoff-iteration-2.md`;
* despliegue backend en GCP y migraciones de producción completados, según evidencia suministrada por el desarrollador;
* producción reportada en `e7a3c9d4f2b1 (head)` después de aplicar `c4f8a1d2e6b9` y `e7a3c9d4f2b1`;
* el preflight de solapamientos funcionó como estaba diseñado: datos de prueba incompatibles fueron saneados de forma controlada antes del reintento exitoso;
* backend disponible para pruebas completas desde consumidores React Native;
* la implementación y los resultados de validación React Native pertenecen a su repositorio independiente; cualquier defecto backend descubierto se atenderá como corrección puntual.

### Planes y suscripciones

La implementación de planes y suscripciones está integrada en `main`.

Componentes observados:

* modelos y migración;
* servicios de suscripción, límites, uso y enforcement;
* endpoints administrativos y de consulta;
* seeds;
* pruebas de servicios y contratos API;
* primera versión del frontend web;
* estabilización de fechas en pruebas de suscripción.

Estado actual:

* backend integrado;
* primera versión web integrada;
* pruebas específicas estabilizadas;
* documentación técnica extensa disponible;
* roadmap histórico pendiente de marcar como completado, parcial o reemplazado.

## Estado de las pruebas

Existen pruebas para:

* aislamiento y seguridad de la base de datos;
* contratos API;
* servicios;
* repositorios;
* permisos seleccionados;
* planes y suscripciones;
* solicitudes de horas extra;
* endpoints web.

`pytest.ini` exige una cobertura global mínima del 80 %, excepto cuando se ejecutan pruebas focalizadas explícitamente con `--no-cov`.

Estado de validación:

* inspección estática del repositorio: realizada;
* pruebas focalizadas finales de horas extra: `113 passed`, `34 warnings`;
* módulo final de horas extra: `124 passed`, `34 warnings`;
* suite backend completa de la rama: `359 passed`, `36 warnings`, `0 failed`;
* validación de migración en `db-test`: downgrade protegido y ciclo limpio OK, cabeza `e7a3c9d4f2b1`;
* typecheck web: pendiente;
* lint web: pendiente;
* build web: pendiente;
* validación manual mobile: externa a este repositorio.
* corrección `ORDEN-DELETE-001`: focalizadas de modelo/servicio `13 passed`, `32 warnings`; ciclo `downgrade e7a3c9d4f2b1 → upgrade head` e inspección de FK OK.
* suite backend actual: `378 passed`, `38 warnings`; la integración overtime anteriormente dependiente del calendario usa ahora un reloj determinista inyectado, con base UTC dentro de la semana de la solicitud y marcas distintas por mutación.

## Estado del despliegue

### Backend

`.github/workflows/ci.yml`:

* se activa mediante push a `main` para cambios backend seleccionados;
* construye una imagen Docker;
* publica la imagen;
* despliega en Cloud Run.

El workflow actual no ejecuta pruebas antes del despliegue, aunque se denomina `CI - CD`.

La segunda iteración backend de horas extra está integrada en `main` y desplegada en GCP. Según la
evidencia de producción suministrada por el desarrollador, las migraciones se aplicaron correctamente
y la revisión efectiva es `e7a3c9d4f2b1 (head)`. Esta sesión no accedió a producción; verificó
localmente Git, código, migraciones, contratos y documentación.

El siguiente punto backend es atender únicamente hallazgos reales de las pruebas integradas mobile o
continuar con otro ítem priorizado del tablero.

### Frontend web

El frontend web se despliega de forma independiente en Vercel utilizando `apps/web` como directorio raíz.

El workflow backend no valida ni despliega automáticamente los cambios de `apps/web`.

La interfaz administrativa de carga de plantillas de checklist está implementada en la rama
`feature/web-admin-checklist-upload`:

* ruta protegida `/dashboard/admin/checklists` con `RoleGuard` para `admin`;
* navegación admin de escritorio y móvil mediante `DashboardShell`, sin enlaces para otros roles;
* lectura local de un único JSON (límite UX de 1 MiB), validación Zod, previsualización responsive y confirmación antes del envío;
* servicio y mutación React Query sin reintentos automáticos para `POST /api/checklists/templates`;
* allowlist limitada exactamente a `/api/checklists/templates`, sin abrir otros endpoints core de checklists;
* typecheck, lint y build web completados correctamente.

La misma pantalla ahora lista el catálogo global mediante `GET /api/checklists/templates`, protegido
para `admin`. El backend devuelve nombres opcionales de tipos con `LEFT OUTER JOIN`, carga los
pasos sin N+1 mediante `selectinload`, conserva IDs cuando falta un catálogo y ordena plantillas y
pasos de forma determinista. La web muestra estados de carga, vacío y error, pasos expandibles y
bloquea una carga local cuando identifica una combinación ya ocupada; tras `201` o `409` invalida
el listado para reflejar el estado del backend.

Las focalizadas del listado (`5 passed`) y la regresión de contrato mobile checklist (`14 passed`)
pasaron. La suite completa posterior alcanzó `378 passed`, `38 warnings`; la integración overtime
preexistente se estabilizó mediante un reloj determinista inyectado. La creación real con un admin y la confirmación de errores `409`/`422` siguen
pendientes de validación manual contra un backend autorizado. No se modificaron migraciones, mobile
ni los archivos JSON/ZIP de trabajo no rastreados.

## Riesgos activos

1. **Crítico — despliegue sin pruebas automáticas**

   El pipeline backend puede desplegar en producción sin ejecutar la suite de pruebas.

2. **Alto — historial Alembic no reproducible desde cero**

   La base de pruebas requiere temporalmente `create_all + stamp`. Debe diseñarse una baseline compatible con las bases existentes.

3. **Alto — endpoints públicos legacy**

   La auditoría identifica endpoints sin protección explícita. Deben tratarse gradualmente sin romper el contrato mobile.

4. **Medio — convivencia de `create_all` y Alembic**

   `Base.metadata.create_all` continúa activo durante el startup de desarrollo.

5. **Medio — documentación histórica de planes**

   Parte de la documentación describe como futuros elementos que ya están implementados.

6. **Medio — README desactualizado**

   `README.md` todavía describe el repositorio como un skeleton genérico y contiene comandos antiguos.

7. **Medio — validación del lint web**

   El script `npm run lint` utiliza `next lint`. Debe comprobarse su compatibilidad con la versión efectiva de Next.js instalada.

8. **Medio — frontend web fuera del pipeline backend**

   Los cambios de `apps/web` no activan las validaciones del workflow actual.

9. **Medio — unicidad de plantillas no reforzada en base de datos**

   La combinación global `tipo_orden_id + tipo_unidad_id` se verifica en el servicio, pero la tabla
   no tiene una constraint que la garantice ante creaciones concurrentes. Requiere la tarea `CHK-001`
   y una migración planificada; no se abordó incidentalmente en esta interfaz.

## Próximo punto de inicio

### Validación manual de listado y carga administrativa de checklists

1. Iniciar sesión web con un usuario `admin`, revisar las plantillas existentes y expandir sus pasos.
2. Seleccionar `docs/checklist_diagnostico_certificacion_ascensor_mrl_otis.json` y confirmar la previsualización de sus 22 pasos.
3. Si su combinación existe, comprobar la identificación, el bloqueo del POST y el salto a la tarjeta correspondiente.
4. Crear una combinación libre y confirmar que aparece al refrescar el listado; repetirla para comprobar el `409` legible.
5. Validar JSON inválido, usuario de otro rol, estado vacío y comportamiento responsive.

### Handoff e implementación React Native

1. Usar `docs/overtime-mobile-handoff-iteration-2.md` como fuente contractual principal.
2. Implementar primero tipos, servicio HTTP, query keys y compatibilidad de enums.
3. Continuar con edición/cancelación, paginación/filtros y exportaciones en los slices propuestos.
4. Validar con este backend en un entorno local o controlado.
5. Mantener migraciones, deploy y distribución mobile sujetos a autorización y secuencia coordinada.

### Prioridad posterior

Después de confirmar una línea base verde:

1. incorporar pruebas backend obligatorias antes del despliegue;
2. actualizar el README;
3. reconciliar la documentación histórica de planes;
4. implementar React Native desde el handoff y validar manualmente los Slices 1–6 en conjunto;
5. diseñar por separado la baseline de Alembic.

## Validaciones de esta revisión

* Contenido del ZIP inspeccionado: sí.
* Ausencia de secretos evidentes en el ZIP: validada.
* Rama y sincronización con `origin/main`: validadas.
* Integración backend de horas extra: confirmada mediante historial Git.
* Integración de planes y suscripciones: confirmada mediante historial Git y código.
* Suite backend completa actual: `359 passed`, `36 warnings`, `0 failed`.
* Estado real de Alembic en `db-test`: `e7a3c9d4f2b1 (head)`, downgrade protegido y ciclo limpio OK.
* Typecheck web: OK (`npm run typecheck`).
* Lint web: OK (`npm run lint`); Next.js informó la deprecación futura de `next lint`, sin errores.
* Build web: OK (`npm run build`).
* Focalizadas backend de listado checklist: `5 passed`, `36 warnings`.
* Regresión móvil de checklist: `14 passed`, `36 warnings`.
* Suite backend completa posterior: `378 passed`, `38 warnings`; integración overtime estabilizada con reloj determinista inyectado.
* Despliegue actual en producción: no confirmado.
* Validación manual: no ejecutada.
