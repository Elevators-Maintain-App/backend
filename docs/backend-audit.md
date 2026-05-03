# VertiOne Backend Audit

Static audit of the FastAPI backend. Scope: enumerate exposed endpoints, map routers/services/dependencies, identify duplicated legacy vs newer services, startup/performance risks, test gaps, deprecation candidates, and architecture inconsistencies. No application behavior was changed.

## Endpoints inventory

Total exposed FastAPI endpoints found in `app/main.py` plus registered routers: **137** including `GET /`.

Legend: `Auth` means the endpoint declares `get_current_firebase_user` or `require_role(...)` in the route signature/decorator. Some endpoints may still perform checks inside services, but that is not visible at the route boundary.

| Method | Path | Router | Handler | Auth / roles |
| --- | --- | --- | --- | --- |
| GET | `/` | `app.main` | `health_check` | none |
| GET | `/api/dashboard/usuarios` | `admin_dashboard.py` | `get_usuarios` | none |
| GET | `/api/dashboard/estadisticas/usuarios` | `admin_dashboard.py` | `get_estadisticas_usuarios` | none |
| GET | `/api/checklists/{orden_id}/template` | `checklists.py` | `get_template` | `technician` |
| GET | `/api/checklists/{orden_id}/load` | `checklists.py` | `load_checklist` | `technician`, `supervisor` |
| GET | `/api/checklists/{orden_id}` | `checklists.py` | `get_checklist` | `technician`, `supervisor` |
| PATCH | `/api/checklists/{orden_id}/items/{step_number}` | `checklists.py` | `update_checklist_item` | `technician`, `supervisor` |
| POST | `/api/checklists/templates` | `checklists.py` | `create_template` | `admin` |
| GET | `/api/checklists/{orden_id}/reporte.pdf` | `checklists.py` | `generar_reporte_pdf` | none |
| GET | `/api/clientes` | `clientes.py` | `get_clientes` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/clientes/{cliente_id}` | `clientes.py` | `get_cliente` | `superAdmin`, `admin`, `supervisor`, `technician` |
| POST | `/api/clientes` | `clientes.py` | `create_cliente` | `superAdmin`, `admin`, `supervisor` |
| PUT | `/api/clientes/{cliente_id}` | `clientes.py` | `update_cliente` | `superAdmin`, `admin`, `supervisor` |
| DELETE | `/api/clientes/{cliente_id}` | `clientes.py` | `delete_cliente` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/clientes/{cliente_id}/proyectos` | `clientes.py` | `get_proyectos_cliente` | none |
| GET | `/api/clientes/{cliente_id}/unidades` | `clientes.py` | `get_unidades_cliente` | none |
| GET | `/api/clientes/{cliente_id}/ordenes-trabajo` | `clientes.py` | `get_ordenes_cliente` | none |
| GET | `/api/companias` | `compania.py` | `get_companias` | `superAdmin` |
| GET | `/api/companias/count` | `compania.py` | `count_companias` | `superAdmin` |
| GET | `/api/companias/users/count` | `compania.py` | `count_users_per_company` | `superAdmin` |
| POST | `/api/companias` | `compania.py` | `create_compania` | `superAdmin` |
| GET | `/api/companias/{compania_id}` | `compania.py` | `get_compania` | `superAdmin` |
| PUT | `/api/companias/{compania_id}` | `compania.py` | `update_compania` | `superAdmin` |
| DELETE | `/api/companias/{compania_id}` | `compania.py` | `delete_compania` | `superAdmin` |
| GET | `/api/companias/documento/{documento}` | `compania.py` | `read_compania_by_documento` | `superAdmin` |
| GET | `/api/companias/tipo-documento/{tipo_documento_id}` | `compania.py` | `read_companias_by_tipo_documento` | `superAdmin` |
| GET | `/api/companias/{compania_id}/users` | `compania.py` | `get_users_by_company` | `superAdmin` |
| DELETE | `/api/companias/{compania_id}/users` | `compania.py` | `delete_users_by_company` | `superAdmin` |
| GET | `/api/dashboard/superadmin` | `dashboard.py` | `get_super_admin_dashboard` | `superAdmin` |
| GET | `/api/dashboard/admin` | `dashboard.py` | `get_admin_dashboard` | `superAdmin`, `admin` |
| GET | `/api/dashboard/supervisor` | `dashboard.py` | `get_supervisor_dashboard` | `superAdmin`, `supervisor` |
| GET | `/api/dashboard/supervisorV2` | `dashboard.py` | `dashboard_supervisor` | `supervisor` |
| GET | `/api/dashboard/tecnico` | `dashboard.py` | `get_tecnico_dashboard` | `superAdmin`, `tecnico` |
| GET | `/api/dashboard/technician` | `dashboard.py` | `dashboard_tecnico` | `technician` |
| GET | `/api/dashboard/cliente` | `dashboard.py` | `get_cliente_dashboard` | `superAdmin`, `client` |
| GET | `/api/dashboard/ordenes-trabajo/resumen` | `dashboard.py` | `get_resumen_ordenes_trabajo` | none |
| GET | `/api/dashboard/unidades/mantenimiento-pendiente` | `dashboard.py` | `get_unidades_mantenimiento_pendiente` | none |
| GET | `/api/dashboard/estadisticas/general` | `dashboard.py` | `get_estadisticas_generales` | none |
| GET | `/api/estados-orden` | `estados_orden.py` | `get_estados_orden` | none |
| GET | `/api/estados-orden/{estado_orden_id}` | `estados_orden.py` | `get_estado_orden` | none |
| POST | `/api/estados-orden` | `estados_orden.py` | `create_estado_orden` | none |
| GET | `/api/hojas-vida` | `hojas_de_vida.py` | `get_hojas_de_vida` | none |
| GET | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | `get_hoja_de_vida` | none |
| POST | `/api/hojas-vida` | `hojas_de_vida.py` | `create_hoja_de_vida` | none |
| PUT | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | `update_hoja_de_vida` | none |
| DELETE | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | `delete_hoja_de_vida` | none |
| GET | `/api/lov/roles` | `lov.py` | `get_roles` | Firebase user |
| GET | `/api/lov/companias` | `lov.py` | `get_companias` | `superAdmin` |
| GET | `/api/lov/niveles-tecnicos` | `lov.py` | `get_nivel_tecnico` | none |
| GET | `/api/lov/paises` | `lov.py` | `get_paises` | none |
| GET | `/api/lov/tipos-documento` | `lov.py` | `get_tipos_documento` | none |
| GET | `/api/lov/tipos-unidad` | `lov.py` | `get_tipos_unidad` | none |
| GET | `/api/lov/prioridades` | `lov.py` | `get_prioridades` | none |
| GET | `/api/lov/tipos-orden` | `lov.py` | `get_tipos_orden` | none |
| GET | `/api/lov/clientes` | `lov.py` | `get_clientes` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/lov/proyectos` | `lov.py` | `get_proyectos` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/lov/unidades` | `lov.py` | `get_unidades` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/lov/tecnicos` | `lov.py` | `get_tecnicos` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/lov/supervisores` | `lov.py` | `get_supervisores` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/niveles-tecnicos` | `nivel_tecnico.py` | `get_nivel_tecnico` | none |
| POST | `/api/niveles-tecnicos` | `nivel_tecnico.py` | `create_nivel_tecnico` | `admin`, `superAdmin`, `supervisor` |
| PUT | `/api/niveles-tecnicos/{nivel_tecnico_id}` | `nivel_tecnico.py` | `update_nivel_tecnico` | `admin`, `superAdmin`, `supervisor` |
| DELETE | `/api/niveles-tecnicos/{nivel_tecnico_id}` | `nivel_tecnico.py` | `delete_nivel_tecnico` | `admin`, `superAdmin`, `supervisor` |
| GET | `/api/ordenes-trabajo/company/count` | `ordenes_de_trabajo.py` | `count_company_ordenes` | `admin` |
| GET | `/api/ordenes-trabajo/company/all` | `ordenes_de_trabajo.py` | `list_company_ordenes` | `admin` |
| GET | `/api/ordenes-trabajo/supervisor/count` | `ordenes_de_trabajo.py` | `count_mis_ordenes` | `supervisor` |
| GET | `/api/ordenes-trabajo/supervisor/all` | `ordenes_de_trabajo.py` | `list_ordenes_supervisor_filtradas` | `supervisor` |
| GET | `/api/ordenes-trabajo/supervisor/all/full` | `ordenes_de_trabajo.py` | `list_mis_todas` | `supervisor` |
| GET | `/api/ordenes-trabajo/supervisor/counts` | `ordenes_de_trabajo.py` | `counts_by_state_supervisor` | `supervisor` |
| GET | `/api/ordenes-trabajo/supervisor/compliance` | `ordenes_de_trabajo.py` | `monthly_compliance_supervisor` | `supervisor` |
| GET | `/api/ordenes-trabajo/technician/count` | `ordenes_de_trabajo.py` | `count_mis_ordenes_tec` | `technician` |
| GET | `/api/ordenes-trabajo/technician/all` | `ordenes_de_trabajo.py` | `list_mis_ultimas_10_tec` | `technician` |
| GET | `/api/ordenes-trabajo/technician/all/full` | `ordenes_de_trabajo.py` | `list_mis_todas_tec` | `technician` |
| GET | `/api/ordenes-trabajo/technician/counts` | `ordenes_de_trabajo.py` | `counts_by_state_tec` | `technician` |
| GET | `/api/ordenes-trabajo/technician/compliance` | `ordenes_de_trabajo.py` | `monthly_compliance_tec` | `technician` |
| PATCH | `/api/ordenes-trabajo/{orden_id}` | `ordenes_de_trabajo.py` | `update_orden` | `supervisor`, `admin`, `super_admin` |
| DELETE | `/api/ordenes-trabajo/{orden_id}` | `ordenes_de_trabajo.py` | `delete_orden` | `supervisor`, `admin`, `super_admin` |
| GET | `/api/ordenes-trabajo/{orden_id}` | `ordenes_de_trabajo.py` | `get_orden_detail` | Firebase user |
| POST | `/api/ordenes-trabajo` | `ordenes_de_trabajo.py` | `create_company_orden` | `superAdmin`, `admin`, `supervisor`, `technician` |
| POST | `/api/seguimiento/{orden_id}/iniciar` | `ordenes_seguimiento.py` | `iniciar_orden` | `technician` |
| POST | `/api/seguimiento/{orden_id}/pausar` | `ordenes_seguimiento.py` | `pausar_orden` | `technician` |
| POST | `/api/seguimiento/{orden_id}/reanudar` | `ordenes_seguimiento.py` | `reanudar_orden` | `technician` |
| POST | `/api/seguimiento/{orden_id}/validar` | `ordenes_seguimiento.py` | `enviar_orden_a_validacion` | `technician` |
| POST | `/api/seguimiento/{orden_id}/finalizar` | `ordenes_seguimiento.py` | `finalizar_orden` | `supervisor` |
| POST | `/api/seguimiento/{orden_id}/items/{item_id}/completar` | `ordenes_seguimiento.py` | `completar_item` | `technician` |
| POST | `/api/seguimiento/{orden_id}/pasos/{step_number}/completar` | `ordenes_seguimiento.py` | `completar_paso_por_orden` | `technician` |
| GET | `/api/seguimiento/{orden_id}/reporte-prerevision` | `ordenes_seguimiento.py` | `obtener_url_reporte_prerevision` | `supervisor` |
| POST | `/api/seguimiento/{orden_id}/sync-validar` | `ordenes_seguimiento.py` | `sync_checklist_y_enviar_a_validacion` | `technician` |
| POST | `/api/seguimiento/{orden_id}/sync-finalizar` | `ordenes_seguimiento.py` | `sync_checklist_y_finalizar_orden` | `supervisor` |
| GET | `/api/prioridades` | `prioridades.py` | `get_prioridades` | none |
| GET | `/api/prioridades/{prioridad_id}` | `prioridades.py` | `get_prioridad` | none |
| POST | `/api/prioridades` | `prioridades.py` | `create_prioridad` | none |
| GET | `/api/proyectos` | `proyectos.py` | `get_proyectos` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/proyectos/{proyecto_id}` | `proyectos.py` | `get_proyecto_detail` | `admin`, `superAdmin`, `supervisor` |
| POST | `/api/proyectos` | `proyectos.py` | `create_proyecto` | `admin`, `superAdmin` |
| PATCH | `/api/proyectos/{proyecto_id}` | `proyectos.py` | `update_proyecto` | `admin` |
| DELETE | `/api/proyectos/{proyecto_id}` | `proyectos.py` | `delete_proyecto` | `admin` |
| GET | `/api/tipos-documento` | `tipos_documento.py` | `get_tipos_documento` | none |
| GET | `/api/tipos-documento/{tipo_documento_id}` | `tipos_documento.py` | `get_tipo_documento` | none |
| POST | `/api/tipos-documento` | `tipos_documento.py` | `create_tipo_documento` | none |
| GET | `/api/tipos-evidencia` | `tipos_evidencia.py` | `get_tipos_evidencia` | none |
| GET | `/api/tipos-evidencia/{tipo_evidencia_id}` | `tipos_evidencia.py` | `get_tipo_evidencia` | none |
| POST | `/api/tipos-evidencia` | `tipos_evidencia.py` | `create_tipo_evidencia` | none |
| GET | `/api/tipos-orden` | `tipos_orden.py` | `get_tipos_orden` | none |
| GET | `/api/tipos-orden/{tipo_orden_id}` | `tipos_orden.py` | `get_tipo_orden` | none |
| POST | `/api/tipos-orden` | `tipos_orden.py` | `create_tipo_orden` | none |
| GET | `/api/tipos-unidad` | `tipos_unidad.py` | `get_tipos_unidad` | none |
| GET | `/api/tipos-unidad/{tipo_unidad_id}` | `tipos_unidad.py` | `get_tipo_unidad` | none |
| POST | `/api/tipos-unidad` | `tipos_unidad.py` | `create_tipo_unidad` | none |
| GET | `/api/unidades/company/count` | `unidades.py` | `count_company_unidades` | `admin` |
| GET | `/api/unidades/company/all` | `unidades.py` | `list_company_unidades` | `admin`, `supervisor` |
| GET | `/api/unidades/{unidad_id}` | `unidades.py` | `get_unidad_detail` | `admin` |
| POST | `/api/unidades` | `unidades.py` | `create_unidad` | `admin` |
| PUT | `/api/unidades/{unidad_id}` | `unidades.py` | `update_unidad` | `admin` |
| DELETE | `/api/unidades/{unidad_id}` | `unidades.py` | `delete_unidad` | `admin` |
| GET | `/api/usuarios/{uid}` | `usuarios.py` | `obtener_usuario` | none |
| GET | `/api/usuarios` | `usuarios.py` | `get_usuarios` | `superAdmin`, `admin`, `supervisor` |
| POST | `/api/usuarios` | `usuarios.py` | `crear_usuario` | `superAdmin`, `admin`, `supervisor` |
| PUT | `/api/usuarios/{uid}` | `usuarios.py` | `actualizar_usuario` | none |
| DELETE | `/api/usuarios/{uid}` | `usuarios.py` | `eliminar_usuario` | `superAdmin`, `admin`, `supervisor` |
| GET | `/api/usuarios/count` | `usuarios.py` | `count_all_users` | `superAdmin` |
| GET | `/api/usuarios/all` | `usuarios.py` | `list_all_users` | `superAdmin` |
| GET | `/api/usuarios/clients/count` | `usuarios.py` | `count_all_clients` | `superAdmin` |
| GET | `/api/usuarios/clients/all` | `usuarios.py` | `list_all_clients` | `superAdmin` |
| GET | `/api/usuarios/company/count` | `usuarios.py` | `count_company_users` | `admin` |
| GET | `/api/usuarios/company/all` | `usuarios.py` | `list_company_users` | `admin`, `supervisor` |
| GET | `/api/usuarios/clients/company/count` | `usuarios.py` | `count_company_clients` | `admin` |
| GET | `/api/usuarios/clients/company/all` | `usuarios.py` | `list_company_clients` | `admin` |
| GET | `/api/usuarios/all/{uid}` | `usuarios.py` | `get_user_detail` | `superAdmin`, `admin` |
| GET | `/api/usuarios/by-role/{rol}` | `usuarios.py` | `get_usuarios_by_role` | `superAdmin`, `operativo` |
| GET | `/api/usuarios/by-company/{company_id}` | `usuarios.py` | `get_usuarios_by_company` | `superAdmin`, `operativo`, `cliente` |
| GET | `/api/usuarios/{uid}` | `usuarios.py` | `get_usuario` | `superAdmin`, `operativo`, `cliente` |
| GET | `/api/zonas-geograficas` | `zonas_geograficas.py` | `get_zonas_geograficas` | none |
| GET | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | `get_zona_geografica` | none |
| POST | `/api/zonas-geograficas` | `zonas_geograficas.py` | `create_zona_geografica` | none |
| PUT | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | `update_zona_geografica` | none |
| DELETE | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | `delete_zona_geografica` | none |

Coverage note: `tests/` contains repository and usuario service tests only (`tests/test_repositories/test_base_repository.py`, `tests/test_services/test_usuario/*`). No `tests/test_api` or route-level tests were found, so all exposed endpoints should be treated as currently uncovered at API level.

## Services map

| Router | Main service/repository dependencies | Notes |
| --- | --- | --- |
| `admin_dashboard.py` | `AdminDashboardService` | Legacy dashboard endpoints without auth dependency. |
| `checklists.py` | `ChecklistService`, `weasyprint.HTML` | Route imports WeasyPrint directly and renders PDF inline for `/reporte.pdf`. |
| `clientes.py` | `cliente.ClienteService` | Newer domain service with role case factory, plus extra child-resource endpoints without auth. |
| `compania.py` | `CompaniaService`, direct `CompaniaModel` SQL, `usuario_crud` patterns | Mostly service-backed, but has direct route SQL for counts and large user-management blocks. |
| `dashboard.py` | `DashboardService`, `orden_trabajo.OrdenTrabajoService` | Mixes legacy aggregate service and clean order dashboard service. |
| Enum routers | Direct CRUD repositories | `estados_orden`, `prioridades`, `tipos_*` bypass service layer. |
| `hojas_de_vida.py` | `HojaDeVidaService` | Legacy CRUD service. No auth dependency. |
| `lov.py` | `RolService`, `CompaniaService`, `NivelTecnicoService`, `PaisService`, direct CRUD repos, `ClienteService`, `ProyectoService`, legacy `UnidadService`, `TecnicoService`, `SupervisorService` | High fan-in router; mixes service families and direct repositories. |
| `nivel_tecnico.py` | `usuario.NivelTecnicoService` | Thin service. GET is public. |
| `ordenes_de_trabajo.py` | legacy `OrdenDeTrabajoService` | Active order router uses legacy flat service, not `orden_trabajo/orden_trabajo_servicio.py`. |
| `ordenes_seguimiento.py` | `OrdenService`, `ChecklistService`, `generar_y_subir_pdf`, direct SQL in route | Workflow route keeps significant business/query logic in route helpers. |
| `proyectos.py` | `proyectos.ProyectoService`, mapper | Newer domain service with role case factory. |
| `unidades.py` | legacy `UnidadService`, direct route SQL/model lookups | Active unit router uses flat legacy service, not `unidad/unidad_servicio.py`. |
| `usuarios.py` | `UsuarioService`, Firestore client, notification/template imports, direct Firestore streams | Mixes service calls and direct Firebase/Firestore access. Contains duplicate dynamic route. |
| `zonas_geograficas.py` | `ZonaGeograficaService` | Legacy CRUD service. No auth dependency. |

Shared dependencies:

- `get_db` in `app/db/session.py`: async SQLAlchemy session dependency; commits after successful request and rolls back on exception.
- `get_current_firebase_user` and `require_role` in `app/auth/firebase.py`: Firebase token verification, Firestore user resolution, role guard.
- `firebase_config` in `app/config/firebase_config.py`: initializes Firebase Admin at module import time.
- SQLAlchemy repositories in `app/db/repositories/*`: base CRUD plus some custom eager-loading/filter methods.

## Legacy services

Legacy/flat services still used by active routers:

- `app/services/ordenes_de_trabajo.py`: active service for `/api/ordenes-trabajo/*`. Contains role-specific listing/counting, detail construction, Firestore lookups, create/update/delete, monthly compliance, and filtered supervisor list.
- `app/services/ordenes.py`: active workflow service for `/api/seguimiento/*`.
- `app/services/unidades.py`: active service for `/api/unidades/*`. Contains company-specific CRUD and pagination helper.
- `app/services/checklists.py`: active checklist service for `/api/checklists/*` and sync workflow.
- `app/services/dashboard.py` and `app/services/admin_dashboard.py`: older aggregate/query services still exposed.
- `app/services/hojas_de_vida.py`, `app/services/zonas_geograficas.py`, `app/services/tecnico.py`, `app/services/supervisor.py`: thin legacy services.

Duplicated logic detected:

- Orders: `app/services/ordenes_de_trabajo.py` and `app/services/orden_trabajo/orden_trabajo_servicio.py` both define order CRUD/count/detail/dashboard concepts. The newer service has role case factories but `_build_detail_response` is explicitly incomplete and returns empty relation fields, while the active router uses the legacy service.
- Units: `app/services/unidades.py` and `app/services/unidad/unidad_servicio.py` both define `UnidadService` with similar CRUD, validation, total-count and compatibility methods. The active router imports `app.services.unidades.UnidadService`, so the newer `unidad/` service is not currently the route owner.
- Users: `app/services/usuario/usuarios.py` exists, but `app/api/routes/usuarios.py` also performs direct Firestore list/count/detail operations and manual pagination.
- Dashboards/orders: `app/services/dashboard.py`, `app/services/admin_dashboard.py`, `app/services/ordenes_de_trabajo.py`, and `app/services/orden_trabajo/orden_trabajo_servicio.py` all compute order/user/unit aggregates with different filters and role naming.
- Reports/checklists: `app/api/routes/checklists.py` has inline PDF generation while `app/services/reportes/generar_pdf_service.py` has a separate report generator for background workflows.

## Clean architecture services

The newer domain-service pattern is visible in:

- `app/services/usuario/*`: service + mapper + interfaces + role-specific user cases.
- `app/services/compania/*`: `CompaniaService`, mapper, interfaces and `FabricaDeCompanias`.
- `app/services/cliente/*`: `ClienteService`, mapper, role cases and interface.
- `app/services/proyectos/*`: `ProyectoService`, mapper and role cases.
- `app/services/unidad/*`: newer unit service with `FabricaDeUnidades`; currently not used by active unit router.
- `app/services/orden_trabajo/*`: newer order service with `FabricaDeOrdenesTabajo`; partially used by dashboard V2 endpoints, but not by `/api/ordenes-trabajo/*`.
- `app/services/notificaciones/*`: strategy/factory/provider/template structure for notifications.

This pattern centralizes role filtering and domain permissions better than the flat services. The migration appears incomplete: active routers still depend on legacy services for orders and units, and some routers bypass services entirely.

## Risks

- Public or unauthenticated operational endpoints:
  - CRUD-like enum/reference endpoints are public, including POST endpoints for `estados_orden`, `prioridades`, `tipos_documento`, `tipos_evidencia`, `tipos_orden`, `tipos_unidad`.
  - `hojas_de_vida` and `zonas_geograficas` CRUD endpoints are public.
  - `clientes/{cliente_id}/proyectos`, `/unidades`, `/ordenes-trabajo` are public and expose company/customer operational relationships.
  - `checklists/{orden_id}/reporte.pdf` is public and generates a PDF.
  - `admin_dashboard` legacy endpoints are public.
- Route shadowing in `usuarios.py`: `GET /api/usuarios/{uid}` is declared before static routes like `/count`, `/all`, `/clients/count`, and a second `GET /api/usuarios/{uid}` is declared later. In FastAPI route order matters; the first dynamic path can capture later single-segment static paths and the later duplicate `/{uid}` is likely unreachable.
- Role naming is inconsistent: `superAdmin`, `super_admin`, `technician`, `tecnico`, `client`, `cliente`, `operativo` all appear in route guards or logic. This raises authorization drift risk.
- `require_role` checks `current_user.rol.value`, while several call sites treat role as strings (`user.rol.value`, `user.role`, `usuario_actual.rol in ['admin', ...]`). If Pydantic/Firebase does not normalize consistently, authorization can fail or diverge.
- `get_db` commits at the end of every successful request. Some routes also call `await db.commit()` explicitly, which can split transactional boundaries in workflow endpoints.
- `firebase_config.py` decodes `FIREBASE_SERVICE_ACCOUNT_B64` and writes `firebase-service-account.json` at import time if missing. This is startup side effect and can fail in read-only deployments or accidentally leave credentials on disk.
- Direct Firestore reads in services/routes make multi-company enforcement harder to audit consistently, especially user listing/counting endpoints.

## Performance opportunities

- Startup imports:
  - `app/main.py` imports all routers eagerly.
  - `app/config/firebase_config.py` initializes Firebase Admin at import time.
  - `app/api/routes/checklists.py` imports `weasyprint.HTML` at router import time.
  - `app/api/routes/ordenes_seguimiento.py` imports `generar_y_subir_pdf`, which imports Jinja2, WeasyPrint, Firebase Storage helpers and report models at import time.
  - `app/api/routes/usuarios.py` imports notification service/template modules even when only user CRUD/list endpoints are needed.
- Costly startup initialization:
  - `lifespan` runs `Base.metadata.create_all` in development. With many models or slow DB connection this can make startup noticeably slower and can mask migration drift.
  - SQLAlchemy engine is created at module import time in `app/db/session.py`.
- Potentially costly SQL:
  - `OrdenDeTrabajoService.list_summary_by_supervisor` and `list_summary_by_technician` eager-load unit/project but call `await self.db.get(EstadoOrden, o.estado_id)` inside the result loop, causing N+1 status lookups.
  - `unidades.py` route helper `_map_unidad` performs DB gets for proyecto, cliente and tipo per unit, causing N+1/N+3 behavior for `/api/unidades/company/all`.
  - `reportes/generar_pdf_service.py` loads all checklist items and all latest step tracking rows, then de-duplicates in Python. For large checklists/history, use a window query or per-item latest subquery.
  - `usuarios.py` Firestore count/list endpoints stream entire collections or filtered streams and do manual skip/limit in Python. This doubles reads in paginated endpoints and does not use Firestore cursors/count aggregation.
  - `dashboard.py` performs several independent aggregate queries; some can be consolidated with filtered counts or cached per role/date window.
  - `ordenes_de_trabajo.py` monthly counts use `extract(year/month, OrdenDeTrabajo.fecha)`, which may prevent efficient index use compared to range predicates.
  - `ordenes_de_trabajo.py` creates sequence/reference using `count()` before insert, which can become slow and race-prone under concurrent writes.

## Technical debt

- Endpoint coverage gap: no API tests were found for the 137 exposed endpoints.
- Layering is inconsistent: several routes contain direct SQL or Firestore business logic instead of delegating to services/repositories.
- Direct repository use in routes is common for enum routers and `lov.py`; this keeps behavior thin but bypasses service-level permission conventions.
- Newer domain services are present but not consistently wired into active routers.
- `ordenes_seguimiento.py` includes helper queries, checklist item lookup, signature fallback parsing, state transition orchestration, commits and background PDF scheduling in the route module.
- `usuarios.py` is a very large route module with direct Firestore streams, duplicate route paths, manual pagination and notification imports.
- `logging.basicConfig(...)` is called inside `ordenes_de_trabajo.py` route/service modules, which can unexpectedly affect global logging configuration.
- Some response models are missing (`load_checklist`, dashboard legacy endpoints, several create/update nivel tecnico endpoints), and some routes return raw dict/list payloads.
- Some comments identify “new” or “legacy compatibility” paths but there is no explicit deprecation mechanism in OpenAPI.

## Recommendations

1. Stabilize route surface first:
   - Fix or explicitly deprecate duplicate/shadowed `usuarios.py` routes.
   - Mark legacy dashboard/order/user endpoints as deprecated in OpenAPI before removal.
   - Normalize role names into one canonical set: likely `superAdmin`, `admin`, `supervisor`, `technician`, `client`.

2. Add API-level smoke tests before refactoring:
   - Generate tests that assert every route registers, has expected auth behavior, and does not get shadowed.
   - Prioritize high-risk routes: `usuarios`, `ordenes-trabajo`, `seguimiento`, `checklists`, `clientes`.

3. Finish service ownership migration:
   - Decide whether `orden_trabajo/orden_trabajo_servicio.py` replaces `ordenes_de_trabajo.py`; complete missing detail mapping before switching.
   - Decide whether `unidad/unidad_servicio.py` replaces `unidades.py`; then wire the active router or delete/deprecate one service path.
   - Move direct Firestore listing/counting from `usuarios.py` into `UsuarioService` or a dedicated Firebase user repository.

4. Reduce startup cost:
   - Lazy import WeasyPrint/report generation inside PDF execution paths or isolate PDF routes/workers.
   - Move Firebase credential-file creation out of import side effects.
   - Keep `create_all` strictly development-only and document migration expectations.

5. Improve query shape:
   - Replace per-row `db.get(...)` mapping with eager loading or explicit joins for order/unit list endpoints.
   - Replace month `extract(...)` filters with date range filters.
   - Replace Firestore stream/manual pagination with cursor-based paging or aggregate count APIs where available.

6. Preserve mobile contract while cleaning:
   - Do not rename payload fields for checklists/orders without a mobile contract pass.
   - Add compatibility tests around checklist sync endpoints before moving logic out of routes.
