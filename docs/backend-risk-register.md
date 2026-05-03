# VertiOne Backend Risk Register

Registro de riesgos identificado en la auditoria estatica del backend. Este documento no cambia comportamiento; sirve para priorizar limpieza segura sin romper mobile.

## Escala

- Critico: puede exponer datos operativos, romper mobile o afectar seguridad multiempresa.
- Alto: puede causar autorizacion inconsistente, regresiones de contrato o caidas en rutas clave.
- Medio: afecta performance, mantenibilidad o costo operativo.
- Bajo: deuda documentable con impacto limitado.

## Riesgos

| ID | Riesgo | Severidad | Evidencia | Impacto | Mitigacion sin romper mobile |
| --- | --- | --- | --- | --- | --- |
| R1 | Endpoints publicos operativos | Critico | Rutas sin `get_current_firebase_user`/`require_role`: `admin_dashboard`, dashboards legacy, CRUD de catalogos, `hojas-vida`, `zonas-geograficas`, relaciones publicas de clientes, `usuarios/{uid}` publico y `checklists/{orden_id}/reporte.pdf`. | Exposicion o modificacion de datos sin auth visible en la ruta. Riesgo multiempresa. | Fase 1: observabilidad por ruta. Fase 2: agregar alternativas protegidas o auth compatible solo despues de medir uso mobile. Ver `docs/public-endpoints-security-audit.md`. |
| R2 | Rutas duplicadas o shadowed en `usuarios.py` | Critico | `GET /api/usuarios/{uid}` aparece antes de rutas estaticas como `/count`, `/all`, `/clients/count` y vuelve a declararse al final. FastAPI evalua por orden. | Rutas estaticas o segunda ruta dinamica pueden quedar inalcanzables o responder con handler equivocado. | No reordenar todavia. Agregar pruebas de registro/alcance y logs. Luego definir migracion compatible. |
| R3 | Roles inconsistentes | Alto | Aparecen `superAdmin`, `super_admin`, `technician`, `tecnico`, `client`, `cliente`, `operativo`. | Autorizacion divergente entre rutas, servicios y datos Firebase/Postgres. Mobile puede depender de aliases actuales. | Documentar roles aceptados. No renombrar todavia. Agregar tests de permisos por rol antes de normalizar. |
| R4 | Servicios legacy duplicados | Alto | Ordenes: `services/ordenes_de_trabajo.py` vs `services/orden_trabajo/*`. Unidades: `services/unidades.py` vs `services/unidad/*`. Usuarios con servicio nuevo y logica Firestore directa en ruta. | Refactors pueden conectar servicio incompleto o cambiar respuesta. Riesgo alto para mobile. | Marcar duenos activos. Agregar smoke tests de contrato antes de migrar. Deprecar por fases, no por reemplazo directo. |
| R5 | Imports pesados en startup | Medio | `app/main.py` importa routers eager; `firebase_config.py` inicializa Firebase al import; `checklists.py` importa WeasyPrint; `ordenes_seguimiento.py` importa generador PDF, Jinja2, storage y modelos de reporte. | Startup lento o fragil, especialmente en deploys con filesystem restringido o sin dependencias nativas listas. | Lazy import en rutas PDF/reportes despues de pruebas. Separar worker/reportes cuando sea posible. |
| R6 | Queries N+1 y streams completos | Medio | `list_summary_by_supervisor/technician` consulta estado por orden; `_map_unidad` consulta proyecto, cliente y tipo por unidad; Firestore lista/count con streams completos y paginacion manual. | Latencia alta, mas costo en Firestore y degradacion en companias grandes. | Optimizar con joins/eager loading/cursors manteniendo response shape. Agregar benchmarks o smoke de payload. |
| R7 | PDF/checklist con WeasyPrint cargado temprano | Medio | `checklists.py` importa `weasyprint.HTML` al cargar router; seguimiento importa `generar_y_subir_pdf`, que arrastra WeasyPrint/Jinja2/storage. | Fallas de librerias nativas pueden impedir levantar toda la API aunque no se use PDF. | Lazy import local en endpoints/tareas de PDF y pruebas de smoke de startup. Sin cambiar payload ni rutas. |
| R8 | Commits explicitos dentro de rutas con `get_db` que tambien commitea | Alto | `get_db` commitea al final de request; `ordenes_seguimiento.py` llama `await db.commit()` en workflow. | Transacciones partidas y estados intermedios si falla generacion/sync posterior. | Observar y testear antes de tocar. Unificar frontera transaccional en fase posterior con pruebas de checklist. |
| R9 | Multiempresa dificil de auditar | Alto | Mezcla de require_role, service filters, direct SQL y Firestore directo. Algunas rutas publicas devuelven relaciones cliente/proyecto/unidad/orden. | Posible fuga entre companias o permisos inconsistentes por rol. | Inventario por endpoint de company filter efectivo. Agregar smoke tests por compania antes de cambios de auth. |
| R10 | Cobertura API inexistente | Alto | Auditoria reporta ausencia de `tests/test_api` o pruebas route-level para 137 endpoints. | Limpieza puede romper mobile sin deteccion temprana. | Fase 3: generar smoke tests de registro, auth esperada y response shape minima. |
| R11 | Catalogos mutables publicos | Alto | `POST` de `estados-orden`, `prioridades` y `tipos-*` fueron mitigados con `require_role("superAdmin", "admin")`. Siguen publicos CRUD de `hojas-vida` y `zonas-geograficas`. `PUT /api/usuarios/{uid}` fue mitigado con `require_role("superAdmin", "admin")`. | Mutacion no autorizada de datos base restante. | No bloquear de golpe. Medir uso y crear politica de auth compatible. Priorizar mutaciones publicas restantes despues de fijar tests de contrato. |
| R12 | Reportes/checklists afectan mobile offline y PDF | Alto | Sync endpoints aceptan payload complejo y fallback de firmas desde `evidencia_data`; PDF se genera en ruta y background. | Cambios pequenos pueden romper reintentos offline, firmas o reportes. | Usar skill/flujo de contrato checklist antes de tocar. Fijar fixtures JSON de mobile como pruebas. |

## Legacy protegido

Estos componentes deben marcarse como legacy en documentacion y pruebas, pero no deben cambiar comportamiento todavia.

- `app/services/ordenes_de_trabajo.py`: dueno activo de `/api/ordenes-trabajo/*`.
- `app/services/ordenes.py`: dueno activo de `/api/seguimiento/*`.
- `app/services/unidades.py`: dueno activo de `/api/unidades/*`.
- `app/services/checklists.py`: dueno activo de `/api/checklists/*` y sync.
- `app/services/dashboard.py` y `app/services/admin_dashboard.py`: dashboards legacy todavia expuestos.
- `app/api/routes/usuarios.py`: mezcla servicio nuevo, Firestore directo, rutas duplicadas y rutas legacy.
- `app/api/routes/checklists.py`: PDF inline legacy.
- `app/services/reportes/generar_pdf_service.py`: generacion PDF background usada por seguimiento.

## TODO de documentacion

- TODO: agregar marca OpenAPI `deprecated=True` solo cuando exista decision de deprecacion y pruebas que confirmen que mobile no depende del endpoint.
- TODO: agregar tabla de "dueno activo" por router en la documentacion tecnica.
- TODO: documentar aliases de roles aceptados antes de normalizar.
- TODO: registrar endpoints publicos en observabilidad antes de aplicar auth.
- TODO: crear fixtures de checklist sync desde payloads mobile reales o `docs/checklist*.json`.

## Criterios para cerrar riesgos

- R1/R11 se cierran solo cuando exista auth compatible o reemplazo versionado, con periodo de deprecacion.
- R2 se cierra cuando pruebas demuestren que rutas estaticas y dinamicas de usuarios llegan al handler correcto tras una migracion compatible.
- R3 se cierra cuando exista mapa canonico de roles y adaptadores para aliases legacy.
- R4 se cierra cuando cada router tenga un dueno de servicio unico y el servicio reemplazado este deprecado o eliminado despues de telemetria.
- R5/R7 se cierran cuando la API pueda iniciar sin cargar WeasyPrint/reportes salvo en rutas/tareas que lo necesiten.
- R6 se cierra cuando endpoints listados no hagan consultas por fila ni streams completos para paginacion comun.
- R10 se cierra cuando los 137 endpoints tengan al menos smoke coverage o cobertura equivalente por grupo de ruta.
