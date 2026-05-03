# Backend Performance Notes

Notas de la fase inicial de performance/cold start. El objetivo fue reducir carga temprana sin cambiar rutas, payloads, response models, auth, DB ni contratos mobile.

## Cambios aplicados

- `app/api/routes/checklists.py`: `WeasyPrint` y `Jinja2` ahora se importan dentro de `GET /api/checklists/{orden_id}/reporte.pdf`.
- `app/api/routes/ordenes_seguimiento.py`: el generador PDF de background se resuelve con wrapper lazy. Importar el router de seguimiento ya no importa `app/services/reportes/generar_pdf_service.py` durante startup.
- `app/services/reportes/generar_pdf_service.py`: `WeasyPrint`, `Jinja2` y `subir_pdf_a_storage` se importan dentro de `generar_y_subir_pdf`, justo antes de generar/subir el PDF.
- `app/services/unidades.py` + `app/api/routes/unidades.py`: `/api/unidades/company/all` ahora usa una consulta explicita con `outerjoin` a proyecto, cliente y tipo de unidad. Se elimina el `db.get` por fila que antes hacia `_map_unidad`.
- `app/services/ordenes_de_trabajo.py`: `/api/ordenes-trabajo/company/all` ahora usa una consulta explicita de columnas para `OrdenDeTrabajoSummaryOut`, evitando cargar entidades ORM completas y relaciones joined innecesarias.
- `app/services/orden_trabajo/orden_trabajo_servicio.py`: `/api/dashboard/technician` consolida las tres consultas de metricas en un solo agregado SQL, preservando filtros, categorias, formulas y listado de ordenes.

Impacto esperado:

- Menor costo de cold start para requests no relacionados con PDF.
- Menor riesgo de que dependencias nativas de WeasyPrint impidan importar rutas comunes.
- La carga pesada queda diferida hasta usar PDF inline o tareas de prereporte/reporte final.

## Verificacion de startup

Comando usado para verificar carga diferida:

```bash
docker compose run --rm api python -c "import sys; import app.main; print('weasyprint' in sys.modules); print('app.services.reportes.generar_pdf_service' in sys.modules)"
```

Resultado esperado despues del cambio:

```text
False
False
```

Esto confirma que importar la app principal no carga WeasyPrint ni el modulo de generacion PDF.

## Imports pesados auditados

| Area | Estado | Nota |
| --- | --- | --- |
| WeasyPrint | Lazy aplicado | Cargado solo al generar PDF. |
| Jinja2 en PDF | Lazy aplicado | Cargado solo al renderizar reporte PDF. |
| Generacion PDF background | Lazy aplicado | El router de seguimiento mantiene el mismo callable nominal, pero importa el servicio real en ejecucion. |
| Firebase init | Sin cambio | `app/main.py` inicializa Firebase en startup. Cambiar esto afecta auth/storage global y requiere fase dedicada. |
| Storage/reportes | Lazy parcial | `subir_pdf_a_storage` se importa dentro de `generar_y_subir_pdf`; otros usos de storage para usuarios/clientes quedan fuera de esta fase. |
| Notificaciones/templates | Sin cambio | Potencial carga en usuarios, pero no se toca para evitar cambiar flujos de alta de usuario. |

## Revision N+1 / queries

### `/api/ordenes-trabajo/company/all`

Ruta activa usa `app/services/ordenes_de_trabajo.py::list_summary_by_company`, que delega en repositorio legacy y serializa `OrdenDeTrabajoSummaryOut`.

Riesgo/observacion:

- Servicio activo: `app/services/ordenes_de_trabajo.py::OrdenDeTrabajoService.list_summary_by_company`.
- Repositorio previo: `orden_de_trabajo_crud.get_multi_by_field`.
- Modelo de respuesta: `List[OrdenDeTrabajoSummaryOut]`.
- Campos preservados: `id`, `referencia`, `fecha`, `supervisor_id`, `tecnico_id`, `unidad_id`, `company_id`, `tipo_orden_id`, `estado_id`, `prioridad_id`.
- Auth/filtro preservado: ruta protegida por `require_role("admin")`; filtro por `user.company_id`.
- Ordenamiento: no habia `order_by` explicito y no se agrego uno nuevo.
- Limite implicito preservado: el metodo efectivo `get_multi_by_field` del repositorio aplicaba `offset(0).limit(100)` por defaults; la query explicita conserva `offset(0).limit(100)`.
- Riesgo mitigado: al seleccionar solo columnas se evita materializar `OrdenDeTrabajo` completo y cargar relaciones `lazy="joined"` que no forman parte del response shape.

Verificacion:

```bash
docker compose run --rm api pytest tests/test_api/test_ordenes_company_all_contract.py -q
```

Resultado:

```text
2 passed
```

### `/api/ordenes-trabajo/supervisor/all`

La ruta activa usa `list_ordenes_supervisor_filtradas`, que ya hace joins a unidad, proyecto, estado y checklist y devuelve `OrdenDeTrabajoListOut`.

Riesgo/observacion:

- No se detecta N+1 evidente en el mapping actual.
- Posible mejora futura: revisar indices para filtros por `supervisor_id`, `estado_id`, `created_at`, `tecnico_id`, `cliente_id` y `unidad.proyecto_id`.

### `/api/unidades/company/all`

La ruta activa cargaba unidades y luego `_map_unidad` hacia `db.get` por unidad para proyecto, cliente y tipo.

Riesgo/observacion:

- N+1/N+3 mitigado.
- Se mantuvo la ruta, auth y `response_model=List[UnidadListOut]`.
- Se preservaron los campos de `UnidadListOut`: `id`, `nombre`, `kpi_funcionamiento`, `proyecto`, `cliente`, `tipo_unidad_id`, `tipo_unidad`, `company_id`, `created_at`, `updated_at`.
- Se preservaron defaults visibles `"—"` cuando faltan nombres de proyecto, cliente o tipo.
- No habia `order_by` explicito previo; el cambio no agrega ordenamiento para no cambiar semantica observable.
- El filtro por compania se mantiene con `where(Unidad.company_id == user.company_id)` y la ruta sigue protegida por `require_role("admin", "supervisor")`.

Verificacion:

```bash
docker compose run --rm api pytest tests/test_api/test_unidades_company_all_contract.py -q
```

Resultado:

```text
1 passed
```

### `/api/dashboard/technician`

Ruta activa:

- `app/api/routes/dashboard.py::dashboard_tecnico`.
- Servicio activo: `app/services/orden_trabajo/orden_trabajo_servicio.py::OrdenTrabajoService.get_dashboard_data`.
- `response_model`: `DashboardTecnicoOut`.
- Auth actual: `require_role("technician")`.

Contrato preservado:

- Campos de metricas: `ordenes_programadas`, `ordenes_completadas`, `ordenes_pendientes`, `cumplimiento_decimal`, `cumplimiento_label`, `cumplimiento_str`.
- Lista: `ordenes_en_curso`.
- Campos por orden: `id`, `cliente`, `tecnico`, `proyecto`, `unidad`, `descripcion`, `observaciones`, `estado`, `fecha_programada`, `prioridad`, `tipo_orden`.
- Filtros: `tecnico_id == user.uid`, `company_id == user.company_id`, `fecha >= fecha_inicio`, `fecha <= fecha_fin`.
- Fechas default de la ruta: ultimos 7 dias hasta hoy cuando no se envian query params.
- Estados completados: `[4, 5]`; estados pendientes: `[1, 3, 6]`.
- Formulas: `cumplimiento_decimal = round(completadas / total, 4)` y `cumplimiento_str = int(cumplimiento * 100)%`.
- Ordenamiento: la query mantiene `order_by(OrdenDeTrabajo.fecha.asc())`; despues el servicio conserva el ordenamiento estable por prioridad de estado (`En ejecución`, `En Pausa`, `Pendiente`, `En Validación`, `Cerrada`).
- Limites: no habia limite explicito y no se agrego uno.

Cambio aplicado:

- Antes se ejecutaban tres `COUNT(*)` independientes sobre el mismo `filtro_base`: total, completadas y pendientes.
- Ahora se ejecuta una sola query agregada con `count` + `sum(case(...))` para las mismas categorias.
- Se mantiene sin cambios la query de ordenes y sus `selectinload` a unidad/proyecto, estado, tipo de orden, prioridad, cliente y tecnico.

Riesgo mitigado:

- Menos roundtrips al abrir el dashboard tecnico mobile.
- No se altera semantica de metricas ni estructura de respuesta.

Verificacion:

```bash
docker compose run --rm api pytest tests/test_api/test_dashboard_technician_contract.py -q
```

Resultado:

```text
2 passed
```

### `/api/dashboard/supervisorV2`

Ruta activa:

- `app/api/routes/dashboard.py::dashboard_supervisor`.
- Servicio activo: `app/services/orden_trabajo/orden_trabajo_servicio.py::OrdenTrabajoService.get_dashboard_data_supervisor`.
- `response_model`: `DashboardSupervisorOut`.
- Auth actual: `require_role("supervisor")`.

Contrato preservado:

- Campos de metricas: `ordenes_programadas`, `ordenes_cerradas`, `ordenes_por_validar`, `ordenes_pendientes`, `ordenes_en_ejecucion`, `ordenes_atrasadas`, `cumplimiento_decimal`, `cumplimiento_label`, `cumplimiento_str`.
- Lista: `ordenes`.
- Campos por orden: `id`, `cliente`, `tecnico`, `proyecto`, `unidad`, `descripcion`, `observaciones`, `estado`, `fecha_programada`, `prioridad`, `tipo_orden`.
- Filtros: `supervisor_id == user.uid`, `company_id == user.company_id`, `fecha >= fecha_inicio`, `fecha <= fecha_fin`.
- Fechas default de la ruta: ultimos 7 dias hasta hoy cuando no se envian query params.
- Conteos actuales desde el listado ya cargado: `estado_id == 5` cuenta como cerrada, `4` como por validar, `1` como pendiente, `3` como en ejecucion y `6` como atrasada.
- Formula: `cumplimiento_decimal = round(cerradas / total, 4)` y `cumplimiento_str = int(cumplimiento_pct * 100)%`.
- Ordenamiento: la query mantiene `order_by(OrdenDeTrabajo.fecha.asc())`; despues el servicio conserva el ordenamiento estable por prioridad de estado (`En ejecución`, `En Pausa`, `Pendiente`, `En Validación`, `Cerrada`).
- Limites: no habia limite explicito y no se agrego uno.

Evaluacion de optimizacion:

- Ya usa `selectinload` para relaciones de ordenes listadas.
- El listado completo forma parte del response mobile, por lo que la query de ordenes no se puede eliminar sin cambiar contrato.
- Pasar conteos a una query agregada separada agregaria un roundtrip adicional y duplicaria filtros, sin reducir la carga principal mientras no haya paginacion/limites.
- No se aplica optimizacion de metricas en esta fase para preservar semantica exacta y evitar trabajo duplicado.

Optimización propuesta:

- Agregar limites/paginacion o agregados SQL solo despues de fijar contrato de dashboard con mobile.
- Revisar indices por `tecnico_id`, `supervisor_id`, `company_id`, `fecha`, `estado_id`.

Verificacion:

```bash
docker compose run --rm api pytest tests/test_api/test_dashboard_supervisor_v2_contract.py -q
```

Resultado:

```text
2 passed
```

## Cambios no aplicados deliberadamente

- No se cambia Firebase initialization en startup.
- No se cambia `Base.metadata.create_all`.
- No se optimizan queries legacy con riesgo de alterar orden, defaults, filtros o shape.
- No se toca checklist offline/sync.
