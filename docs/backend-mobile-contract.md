# VertiOne Backend Mobile Contract

Este documento define la superficie de API que debe tratarse como protegida para la app mobile actual durante la limpieza del backend. Es una linea base conservadora basada en la auditoria estatica de `docs/backend-audit.md` y las rutas registradas en `app/main.py`.

No implica que todos estos endpoints sean ideales ni seguros en su estado actual. Implica que no se deben eliminar, renombrar, mover, cambiar payloads, cambiar codigos de respuesta esperados ni alterar filtros visibles para mobile sin una fase de compatibilidad y pruebas.

## Reglas de proteccion

- No cambiar rutas, metodos HTTP ni nombres de parametros.
- No cambiar nombres, tipos ni presencia de campos en request/response.
- No renombrar roles todavia (`technician`, `supervisor`, `admin`, `superAdmin`, `client` y aliases legacy deben seguir funcionando donde ya funcionan).
- No cambiar paginacion, filtros ni ordenamientos sin contrato nuevo.
- No cambiar comportamiento offline/sync de checklists.
- No cambiar generacion o URLs de reportes consumidas por mobile.
- No agregar auth a endpoints publicos operativos sin fase de compatibilidad, aunque esten marcados como riesgo.
- No eliminar endpoints legacy; primero marcar, medir uso y deprecar.

## Endpoints protegidos por dominio

### Salud y bootstrap

| Metodo | Ruta | Motivo |
| --- | --- | --- |
| GET | `/` | Health check actual. |
| GET | `/api/lov/roles` | Bootstrap de roles. |
| GET | `/api/lov/companias` | Selectores administrativos. |
| GET | `/api/lov/niveles-tecnicos` | Selectores de usuarios tecnicos. |
| GET | `/api/lov/paises` | Selectores de companias/usuarios. |
| GET | `/api/lov/tipos-documento` | Selectores de identificacion. |
| GET | `/api/lov/tipos-unidad` | Selectores de unidades. |
| GET | `/api/lov/prioridades` | Selectores de ordenes. |
| GET | `/api/lov/tipos-orden` | Selectores de ordenes. |
| GET | `/api/lov/clientes` | Selectores operativos por rol. |
| GET | `/api/lov/proyectos` | Selectores operativos por rol. |
| GET | `/api/lov/unidades` | Selectores operativos por rol. |
| GET | `/api/lov/tecnicos` | Selectores de asignacion. |
| GET | `/api/lov/supervisores` | Selectores de asignacion. |

### Usuarios y sesion operativa

Estas rutas tienen riesgo de shadowing en `usuarios.py`, pero se deben preservar hasta resolver compatibilidad.

| Metodo | Ruta | Roles/uso observado |
| --- | --- | --- |
| GET | `/api/usuarios` | `superAdmin`, `admin`, `supervisor`; listado paginado. |
| POST | `/api/usuarios` | `superAdmin`, `admin`, `supervisor`; creacion multipart/form-data. |
| GET | `/api/usuarios/{uid}` | Ruta duplicada/shadowed; tratar como contrato protegido legacy. |
| PUT | `/api/usuarios/{uid}` | Actualizacion legacy sin guard visible en ruta. |
| DELETE | `/api/usuarios/{uid}` | `superAdmin`, `admin`, `supervisor`. |
| GET | `/api/usuarios/count` | `superAdmin`; conteo Firebase. |
| GET | `/api/usuarios/all` | `superAdmin`; listado Firebase. |
| GET | `/api/usuarios/all/{uid}` | `superAdmin`, `admin`; detalle Firebase. |
| GET | `/api/usuarios/clients/count` | `superAdmin`; conteo clientes. |
| GET | `/api/usuarios/clients/all` | `superAdmin`; listado clientes. |
| GET | `/api/usuarios/company/count` | `admin`; conteo por compania. |
| GET | `/api/usuarios/company/all` | `admin`, `supervisor`; listado por compania. |
| GET | `/api/usuarios/clients/company/count` | `admin`; conteo clientes por compania. |
| GET | `/api/usuarios/clients/company/all` | `admin`; listado clientes por compania. |
| GET | `/api/usuarios/by-role/{rol}` | `superAdmin`, `operativo`; legacy. |
| GET | `/api/usuarios/by-company/{company_id}` | `superAdmin`, `operativo`, `cliente`; legacy. |

TODO documentacion: marcar `GET /api/usuarios/{uid}`, `GET /api/usuarios/by-role/{rol}` y `GET /api/usuarios/by-company/{company_id}` como legacy/protegidos en futuras notas OpenAPI, sin cambiar comportamiento todavia.

### Dashboards mobile

| Metodo | Ruta | Motivo |
| --- | --- | --- |
| GET | `/api/dashboard/superadmin` | Dashboard por rol. |
| GET | `/api/dashboard/admin` | Dashboard por rol. |
| GET | `/api/dashboard/supervisor` | Dashboard por rol legacy. |
| GET | `/api/dashboard/supervisorV2` | Dashboard supervisor nuevo. |
| GET | `/api/dashboard/tecnico` | Dashboard tecnico legacy con rol `tecnico`. |
| GET | `/api/dashboard/technician` | Dashboard technician nuevo. |
| GET | `/api/dashboard/cliente` | Dashboard cliente. |
| GET | `/api/dashboard/ordenes-trabajo/resumen` | Agregado operativo legacy. |
| GET | `/api/dashboard/unidades/mantenimiento-pendiente` | Agregado operativo legacy. |
| GET | `/api/dashboard/estadisticas/general` | Agregado operativo legacy. |
| GET | `/api/dashboard/usuarios` | Admin dashboard legacy publico. |
| GET | `/api/dashboard/estadisticas/usuarios` | Admin dashboard legacy publico. |

TODO documentacion: tratar `/api/dashboard/usuarios`, `/api/dashboard/estadisticas/usuarios`, `/api/dashboard/tecnico` y los agregados publicos como legacy hasta medir uso real.

### Ordenes de trabajo

| Metodo | Ruta | Roles/uso observado |
| --- | --- | --- |
| GET | `/api/ordenes-trabajo/company/count` | `admin`. |
| GET | `/api/ordenes-trabajo/company/all` | `admin`. |
| GET | `/api/ordenes-trabajo/supervisor/count` | `supervisor`. |
| GET | `/api/ordenes-trabajo/supervisor/all` | `supervisor`; filtros por estado/fecha/cliente/tecnico/proyecto. |
| GET | `/api/ordenes-trabajo/supervisor/all/full` | `supervisor`. |
| GET | `/api/ordenes-trabajo/supervisor/counts` | `supervisor`. |
| GET | `/api/ordenes-trabajo/supervisor/compliance` | `supervisor`. |
| GET | `/api/ordenes-trabajo/technician/count` | `technician`. |
| GET | `/api/ordenes-trabajo/technician/all` | `technician`; ultimas 10. |
| GET | `/api/ordenes-trabajo/technician/all/full` | `technician`. |
| GET | `/api/ordenes-trabajo/technician/counts` | `technician`. |
| GET | `/api/ordenes-trabajo/technician/compliance` | `technician`. |
| GET | `/api/ordenes-trabajo/{orden_id}` | Usuario Firebase; detalle compartido. |
| POST | `/api/ordenes-trabajo` | Creacion actual; devuelve UUID. |
| PATCH | `/api/ordenes-trabajo/{orden_id}` | Edicion actual. |
| DELETE | `/api/ordenes-trabajo/{orden_id}` | Eliminacion actual. |

TODO documentacion: `app/services/ordenes_de_trabajo.py` es el dueno activo legacy de estas rutas. No migrar a `app/services/orden_trabajo/orden_trabajo_servicio.py` sin pruebas de contrato.

### Seguimiento, checklist offline y reportes

Estos endpoints son criticos para mobile offline, cambios de estado y generacion de reportes.

| Metodo | Ruta | Roles/uso observado |
| --- | --- | --- |
| GET | `/api/checklists/{orden_id}/template` | `technician`; plantilla por orden. |
| GET | `/api/checklists/{orden_id}/load` | `technician`, `supervisor`; inicializa checklist. |
| GET | `/api/checklists/{orden_id}` | `technician`, `supervisor`; obtener/inicializar. |
| PATCH | `/api/checklists/{orden_id}/items/{step_number}` | `technician`, `supervisor`; actualizacion parcial. |
| POST | `/api/checklists/templates` | `admin`; administracion de plantillas. |
| GET | `/api/checklists/{orden_id}/reporte.pdf` | PDF legacy publico. |
| POST | `/api/seguimiento/{orden_id}/iniciar` | `technician`. |
| POST | `/api/seguimiento/{orden_id}/pausar` | `technician`. |
| POST | `/api/seguimiento/{orden_id}/reanudar` | `technician`. |
| POST | `/api/seguimiento/{orden_id}/validar` | `technician`; prereporte en background. |
| POST | `/api/seguimiento/{orden_id}/finalizar` | `supervisor`; reporte final en background. |
| POST | `/api/seguimiento/{orden_id}/items/{item_id}/completar` | `technician`; paso por item. |
| POST | `/api/seguimiento/{orden_id}/pasos/{step_number}/completar` | `technician`; paso por numero. |
| GET | `/api/seguimiento/{orden_id}/reporte-prerevision` | `supervisor`; URL/datos prerevision. |
| POST | `/api/seguimiento/{orden_id}/sync-validar` | `technician`; sync offline y validacion. |
| POST | `/api/seguimiento/{orden_id}/sync-finalizar` | `supervisor`; sync offline y cierre. |

TODO documentacion: no cambiar estructura de `ChecklistSyncPayload`, firmas ni fallback de firmas dentro de `evidencia_data` sin validacion mobile.

### Solicitudes de horas extra

La superficie backend de la segunda iteración está integrada y disponible en producción. La
implementación de UI, descarga y validación React Native pertenece al repositorio mobile.

`POST /api/overtime/requests` conserva su payload y respuesta exitosa. Como ampliación compatible, puede devolver `409 Conflict` con `detail` `Ya existe una solicitud activa que se solapa con la fecha y el horario indicados.` cuando el técnico ya tiene una solicitud `pending`, `approved` o `adjusted` que intersecta la misma fecha y franja. Las franjas adyacentes se permiten y una solicitud `rejected` no bloquea.

Se agregan `PATCH /api/overtime/requests/me/{request_id}` para edición parcial propia y `POST /api/overtime/requests/me/{request_id}/cancel` para cancelación sin payload. Ambas operaciones requieren una solicitud `pending`, usan el detalle existente como respuesta y pueden devolver `404` por falta de visibilidad o `409` por estado/solapamiento.

El contrato incorpora el estado `cancelled` y los eventos `edited` y `cancelled`. Un cliente mobile que deserialice enums de forma cerrada debe actualizar unions, etiquetas, historial, formulario, acciones e invalidación de queries antes de un despliegue coordinado que pueda producir estos valores.

Se agregan de forma aditiva `GET /api/overtime/requests/me/page` y `GET /api/overtime/supervisor/requests/page`. Devuelven `items`, `page`, `page_size`, `total`, `total_pages`, `date_from` y `date_to`; admiten un estado y rango de fechas, y supervisor puede filtrar por técnico sin ampliar visibilidad. Los endpoints array con `skip`/`limit` permanecen intactos y no están deprecados. Mobile actual puede seguir usándolos hasta migrar coordinadamente a `/page`.

`GET /api/overtime/supervisor/catalogs/technicians` requiere supervisor activo y devuelve un array
de elementos con exactamente `{ "id": UUID, "name": string }`. Lista únicamente técnicos activos
de su compañía, ordenados por nombre y UUID. El `id` es `usuarios.id` de PostgreSQL y es la fuente
exclusiva para `technician_id` en `/supervisor/requests/page` y `/supervisor/requests/export`.
`/api/lov/tecnicos` conserva su Firebase UID y su contrato legacy para otros dominios; no debe usarse
para filtros overtime.

`GET /api/overtime/supervisor/requests/export` permite la descarga autenticada con Bearer y `format` obligatorio, exactamente `pdf` o `xlsx`. Acepta `date_from`, `date_to`, `status` y `technician_id`, y devuelve directamente una respuesta binaria, no JSON ni URL. PDF usa `application/pdf`, nombre `horas-extra_{date_from}_{date_to}.pdf` y máximo 2000 solicitudes. XLSX usa `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, nombre `horas-extra_{date_from}_{date_to}.xlsx` y máximo 10000; contiene las hojas `Solicitudes`, `Resumen por técnico` y `Resumen general`. Ambos usan `Content-Disposition: attachment` y todo el resultado filtrado, no solo una página. Puede devolver `400` por rango, `403` por autorización, `413` por el límite propio del formato y `422` por formato/parámetros. La descarga y compartición desde React Native se implementa y valida en el repositorio mobile.

### Clientes, proyectos y unidades

| Metodo | Ruta | Motivo |
| --- | --- | --- |
| GET | `/api/clientes` | Listado paginado por rol. |
| GET | `/api/clientes/{cliente_id}` | Detalle. |
| POST | `/api/clientes` | Creacion. |
| PUT | `/api/clientes/{cliente_id}` | Actualizacion. |
| DELETE | `/api/clientes/{cliente_id}` | Eliminacion. |
| GET | `/api/clientes/{cliente_id}/proyectos` | Relacion cliente-proyectos legacy publica. |
| GET | `/api/clientes/{cliente_id}/unidades` | Relacion cliente-unidades legacy publica. |
| GET | `/api/clientes/{cliente_id}/ordenes-trabajo` | Relacion cliente-ordenes legacy publica. |
| GET | `/api/proyectos` | Listado paginado por rol. |
| GET | `/api/proyectos/{proyecto_id}` | Detalle. |
| POST | `/api/proyectos` | Creacion. |
| PATCH | `/api/proyectos/{proyecto_id}` | Actualizacion. |
| DELETE | `/api/proyectos/{proyecto_id}` | Eliminacion. |
| GET | `/api/unidades/company/count` | Conteo por compania. |
| GET | `/api/unidades/company/all` | Listado por compania. |
| GET | `/api/unidades/{unidad_id}` | Detalle. |
| POST | `/api/unidades` | Creacion. |
| PUT | `/api/unidades/{unidad_id}` | Actualizacion. |
| DELETE | `/api/unidades/{unidad_id}` | Eliminacion. |

TODO documentacion: `app/services/unidades.py` es el dueno activo legacy de `/api/unidades/*`. No migrar a `app/services/unidad/unidad_servicio.py` sin pruebas de contrato.

### Companias y administracion

| Metodo | Ruta |
| --- | --- |
| GET | `/api/companias` |
| GET | `/api/companias/count` |
| GET | `/api/companias/users/count` |
| POST | `/api/companias` |
| GET | `/api/companias/{compania_id}` |
| PUT | `/api/companias/{compania_id}` |
| DELETE | `/api/companias/{compania_id}` |
| GET | `/api/companias/documento/{documento}` |
| GET | `/api/companias/tipo-documento/{tipo_documento_id}` |
| GET | `/api/companias/{compania_id}/users` |
| DELETE | `/api/companias/{compania_id}/users` |

### Catalogos y entidades publicas legacy

Estos endpoints tienen riesgo por auth ausente, pero se preservan hasta tener reemplazos protegidos y compatibilidad.

| Metodo | Ruta |
| --- | --- |
| GET | `/api/estados-orden` |
| GET | `/api/estados-orden/{estado_orden_id}` |
| POST | `/api/estados-orden` |
| GET | `/api/prioridades` |
| GET | `/api/prioridades/{prioridad_id}` |
| POST | `/api/prioridades` |
| GET | `/api/tipos-documento` |
| GET | `/api/tipos-documento/{tipo_documento_id}` |
| POST | `/api/tipos-documento` |
| GET | `/api/tipos-evidencia` |
| GET | `/api/tipos-evidencia/{tipo_evidencia_id}` |
| POST | `/api/tipos-evidencia` |
| GET | `/api/tipos-orden` |
| GET | `/api/tipos-orden/{tipo_orden_id}` |
| POST | `/api/tipos-orden` |
| GET | `/api/tipos-unidad` |
| GET | `/api/tipos-unidad/{tipo_unidad_id}` |
| POST | `/api/tipos-unidad` |
| GET | `/api/niveles-tecnicos` |
| POST | `/api/niveles-tecnicos` |
| PUT | `/api/niveles-tecnicos/{nivel_tecnico_id}` |
| DELETE | `/api/niveles-tecnicos/{nivel_tecnico_id}` |
| GET | `/api/hojas-vida` |
| GET | `/api/hojas-vida/{hoja_id}` |
| POST | `/api/hojas-vida` |
| PUT | `/api/hojas-vida/{hoja_id}` |
| DELETE | `/api/hojas-vida/{hoja_id}` |
| GET | `/api/zonas-geograficas` |
| GET | `/api/zonas-geograficas/{zona_id}` |
| POST | `/api/zonas-geograficas` |
| PUT | `/api/zonas-geograficas/{zona_id}` |
| DELETE | `/api/zonas-geograficas/{zona_id}` |

TODO documentacion: marcar catalogos mutables publicos, `hojas-vida` y `zonas-geograficas` como legacy/public-risk en OpenAPI o changelog interno antes de cualquier cambio de auth.

## Antes de tocar un endpoint protegido

1. Confirmar si mobile lo consume actualmente mediante logs, analytics, proxy o version de app.
2. Agregar smoke test que fije metodo, path, auth esperada, parametros principales y shape de respuesta.
3. Si se requiere cambio, crear endpoint/version nueva o compatibilidad temporal.
4. Mantener el endpoint viejo hasta completar deprecacion controlada.
5. Documentar impacto en `docs/backend-risk-register.md` y roadmap.
