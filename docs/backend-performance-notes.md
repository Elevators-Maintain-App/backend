# Backend Performance Notes

Notas de la fase inicial de performance/cold start. El objetivo fue reducir carga temprana sin cambiar rutas, payloads, response models, auth, DB ni contratos mobile.

## Cambios aplicados

- `app/api/routes/checklists.py`: `WeasyPrint` y `Jinja2` ahora se importan dentro de `GET /api/checklists/{orden_id}/reporte.pdf`.
- `app/api/routes/ordenes_seguimiento.py`: el generador PDF de background se resuelve con wrapper lazy. Importar el router de seguimiento ya no importa `app/services/reportes/generar_pdf_service.py` durante startup.
- `app/services/reportes/generar_pdf_service.py`: `WeasyPrint`, `Jinja2` y `subir_pdf_a_storage` se importan dentro de `generar_y_subir_pdf`, justo antes de generar/subir el PDF.

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

- No se aplica cambio aun porque depende del comportamiento exacto de `orden_de_trabajo_crud.get_multi_by_field`.
- Posible mejora: usar query explicita con columnas/orden estable o eager loading solo si se confirma que el repositorio genera lazy loads.

### `/api/ordenes-trabajo/supervisor/all`

La ruta activa usa `list_ordenes_supervisor_filtradas`, que ya hace joins a unidad, proyecto, estado y checklist y devuelve `OrdenDeTrabajoListOut`.

Riesgo/observacion:

- No se detecta N+1 evidente en el mapping actual.
- Posible mejora futura: revisar indices para filtros por `supervisor_id`, `estado_id`, `created_at`, `tecnico_id`, `cliente_id` y `unidad.proyecto_id`.

### `/api/unidades/company/all`

La ruta activa carga unidades y luego `_map_unidad` hace `db.get` por unidad para proyecto, cliente y tipo.

Riesgo/observacion:

- N+1/N+3 probable.
- No se aplica en esta fase porque cambiar el query requiere validar relaciones/modelos y preservar exactamente `UnidadListOut`.
- Optimización propuesta: reemplazar mapping por query con joins/eager loading a `Proyecto`, `Cliente` y `TipoUnidad`, manteniendo los mismos defaults (`"—"`) y campos.

### Dashboards `technician` y `supervisorV2`

Usan `app/services/orden_trabajo/orden_trabajo_servicio.py`.

Riesgo/observacion:

- Ya usan `selectinload` para relaciones de ordenes listadas.
- `technician` ejecuta tres counts independientes mas una query de ordenes. Puede consolidarse con agregados condicionales, pero eso toca logica de metricas.
- `supervisorV2` carga ordenes y calcula conteos en Python. Puede ser correcto para listas pequenas, pero costoso para ventanas grandes.

Optimización propuesta:

- Agregar limites/paginacion o agregados SQL solo despues de fijar contrato de dashboard con mobile.
- Revisar indices por `tecnico_id`, `supervisor_id`, `company_id`, `fecha`, `estado_id`.

## Cambios no aplicados deliberadamente

- No se cambia Firebase initialization en startup.
- No se cambia `Base.metadata.create_all`.
- No se optimizan queries legacy con riesgo de alterar orden, defaults, filtros o shape.
- No se toca checklist offline/sync.
