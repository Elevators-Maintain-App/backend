# Handoff mobile — horas extra, iteración 2

## 1. Estado del backend

La segunda iteración backend está implementada y probada localmente en la rama
`feature/overtime-iteration-2-backend`. Los Slices 1–6 permanecen en el working tree, sin commit
propio, merge, push ni deploy. No deben consumirse todavía como capacidades disponibles en
producción.

Migraciones pendientes de integración y despliegue coordinado:

- `c4f8a1d2e6b9`: restricción GiST contra solapamientos activos;
- `e7a3c9d4f2b1`: estado `cancelled` y eventos `edited`/`cancelled`.

La cabeza esperada y verificada es `e7a3c9d4f2b1`. La validación final reunió `359 passed`,
`36 warnings` y `0 failed`; la diferencia de una prueba frente al Slice 5 corresponde al contrato
OpenAPI consolidado. La validación manual con React Native/Expo está pendiente.

Todos los endpoints usan Bearer token Firebase. El backend resuelve el usuario operativo y la
compañía desde Firebase/PostgreSQL; mobile nunca envía `company_id`, identidad del técnico, estado,
revisor ni minutos calculados.

## 2. Matriz contractual consolidada

Prefijo común: `/api/overtime`.

| Método | Ruta | Rol | Request/query | Respuesta | Errores relevantes | Impacto mobile |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/catalogs/projects` | `technician` | Sin parámetros | `OvertimeCatalogItem[]` | 401, 403 | Fuente del selector de proyecto. |
| GET | `/catalogs/supervisors` | `technician` | Sin parámetros | `OvertimeCatalogItem[]` | 401, 403 | Fuente del supervisor autorizante. |
| POST | `/requests` | `technician` | `OvertimeRequestCreate` | `201 OvertimeRequestDetail` | 400, 401, 403, 409, 422 | Crear y refrescar listas propias. |
| GET | `/requests/me` | `technician` | `status?`, `date_from?`, `date_to?`, `skip=0`, `limit=20` | `OvertimeRequestSummary[]` | 400, 401, 403, 422 | Contrato array legacy preservado. |
| GET | `/requests/me/page` | `technician` | `status?`, `date_from?`, `date_to?`, `page=1`, `page_size=20` | `OvertimeRequestPage` | 400, 401, 403, 422 | Destino recomendado para la iteración 2. |
| GET | `/requests/me/{request_id}` | `technician` | UUID path | `OvertimeRequestDetail` | 401, 403, 404, 422 | Detalle e historial propio. |
| PATCH | `/requests/me/{request_id}` | `technician` | `OvertimeRequestUpdate` parcial | `OvertimeRequestDetail` | 400, 401, 403, 404, 409, 422 | Formulario de edición solo `pending`. |
| POST | `/requests/me/{request_id}/cancel` | `technician` | Sin body | `OvertimeRequestDetail` | 401, 403, 404, 409, 422 | Cancelación lógica e invalidación de listas/detalle. |
| GET | `/supervisor/requests` | `supervisor` | Filtros anteriores, `technician_id?`, `skip`, `limit` | `OvertimeRequestSummary[]` | 400, 401, 403, 422 | Contrato array legacy preservado. |
| GET | `/supervisor/requests/page` | `supervisor` | `status?`, `technician_id?`, rango, `page`, `page_size` | `OvertimeRequestPage` | 400, 401, 403, 422 | Listado recomendado para iteración 2. |
| GET | `/supervisor/requests/export` | `supervisor` | `format=pdf|xlsx` obligatorio; filtros sin paginación | Bytes PDF/XLSX | 400, 401, 403, 413, 422 | Descargar a archivo y abrir/compartir. |
| GET | `/supervisor/requests/{request_id}` | `supervisor` | UUID path | `OvertimeRequestDetail` | 401, 403, 404, 422 | Solo solicitudes asignadas. |
| POST | `/supervisor/requests/{request_id}/approve` | `supervisor` | `{ "note": string|null }` | `OvertimeRequestDetail` | 401, 403, 404, 409, 422 | Invalidar listas y detalle. |
| POST | `/supervisor/requests/{request_id}/adjust-and-approve` | `supervisor` | Horario completo, actividad, proyecto y nota | `OvertimeRequestDetail` | 400, 401, 403, 404, 409, 422 | Corrección final; no cambia fecha ni supervisor. |
| POST | `/supervisor/requests/{request_id}/reject` | `supervisor` | `{ "note": string }` | `OvertimeRequestDetail` | 401, 403, 404, 409, 422 | Nota obligatoria; invalidar listas/detalle. |

`OvertimeCatalogItem` contiene exactamente `id` UUID y `name` string.

## 3. Payloads y respuestas exactas

### Creación

```json
{
  "work_date": "2026-07-15",
  "entry_time": "07:00",
  "break_start_time": "12:00",
  "break_end_time": "12:30",
  "exit_time": "17:00",
  "activity": "Mantenimiento preventivo",
  "project_id": "55555555-5555-5555-5555-555555555555",
  "authorizing_supervisor_id": "44444444-4444-4444-4444-444444444444"
}
```

El receso puede omitirse enviando ambos extremos como `null`. No se aceptan campos extra.

### PATCH parcial

```json
{
  "activity": "Mantenimiento preventivo y pruebas",
  "exit_time": "18:00",
  "authorizing_supervisor_id": "77777777-7777-7777-7777-777777777777"
}
```

Los campos omitidos conservan su valor. `work_date`, `entry_time`, `exit_time`, `activity`,
`project_id` y `authorizing_supervisor_id` no admiten `null`. Para retirar el receso se deben enviar
ambos campos explícitamente:

```json
{
  "break_start_time": null,
  "break_end_time": null
}
```

Un objeto vacío o un solo extremo de receso que deje inválido el objeto final se rechaza.

### Detalle

```json
{
  "id": "66666666-6666-6666-6666-666666666666",
  "work_date": "2026-07-15",
  "activity": "Mantenimiento preventivo y pruebas",
  "project": {
    "id": "55555555-5555-5555-5555-555555555555",
    "name": "Proyecto Norte"
  },
  "technician": {
    "id": "33333333-3333-3333-3333-333333333333",
    "name": "Técnico Uno"
  },
  "authorizing_supervisor": {
    "id": "44444444-4444-4444-4444-444444444444",
    "name": "Supervisor Uno"
  },
  "worked_minutes": 630,
  "regular_minutes": 480,
  "overtime_minutes": 150,
  "status": "pending",
  "submitted_at": "2026-07-15T22:05:00Z",
  "reviewed_at": null,
  "entry_time": "07:00:00",
  "break_start_time": "12:00:00",
  "break_end_time": "12:30:00",
  "exit_time": "18:00:00",
  "supervisor_note": null,
  "created_at": "2026-07-15T22:05:00Z",
  "updated_at": "2026-07-15T22:10:00Z",
  "events": []
}
```

Pydantic serializa `time` como string ISO; mobile debe aceptar `HH:MM:SS` aunque los payloads pueden
usar `HH:MM`. Los timestamps son ISO 8601 con zona.

### Eventos de edición y cancelación

```json
{
  "id": "88888888-8888-8888-8888-888888888888",
  "actor_user_id": "33333333-3333-3333-3333-333333333333",
  "event_type": "edited",
  "previous_status": "pending",
  "new_status": "pending",
  "note": null,
  "snapshot_before": {
    "status": "pending",
    "activity": "Mantenimiento preventivo"
  },
  "snapshot_after": {
    "status": "pending",
    "activity": "Mantenimiento preventivo y pruebas"
  },
  "created_at": "2026-07-15T22:10:00Z"
}
```

```json
{
  "id": "99999999-9999-9999-9999-999999999999",
  "actor_user_id": "33333333-3333-3333-3333-333333333333",
  "event_type": "cancelled",
  "previous_status": "pending",
  "new_status": "cancelled",
  "note": null,
  "snapshot_before": {
    "status": "pending"
  },
  "snapshot_after": {
    "status": "cancelled"
  },
  "created_at": "2026-07-15T22:12:00Z"
}
```

Los snapshots reales contienen además IDs, fecha, horarios, actividad, minutos, revisión y nota. La
UI debe tratarlos como datos de auditoría (`Record<string, unknown>`), no como payload editable.

### Respuesta paginada

```json
{
  "items": [],
  "page": 2,
  "page_size": 20,
  "total": 0,
  "total_pages": 0,
  "date_from": "2026-06-15",
  "date_to": "2026-07-15"
}
```

`items` usa `OvertimeRequestSummary`: los campos del detalle desde `entry_time` hasta `events` no
están presentes.

### Errores relevantes

Solapamiento en creación o edición:

```json
{
  "detail": "Ya existe una solicitud activa que se solapa con la fecha y el horario indicados."
}
```

Conflictos de estado usan `409` con `La solicitud ya no está pendiente` para mutaciones técnicas o
`La solicitud ya fue resuelta` para revisión del supervisor.

Exceso XLSX (`10001` o más):

```json
{
  "detail": "El reporte supera el máximo de 10000 solicitudes para XLSX. Reduce el período o aplica más filtros."
}
```

PDF sobre 2000 usa `413` y `El reporte supera el máximo de 2000 solicitudes. Reduce el período o
aplica más filtros.`

## 4. Enums y etiquetas

Valores contractuales de estado:

- `pending`
- `approved`
- `adjusted`
- `rejected`
- `cancelled`

Valores contractuales de evento:

- `submitted`
- `edited`
- `approved`
- `adjusted_and_approved`
- `rejected`
- `cancelled`

Etiquetas UI sugeridas, no parte del contrato: Pendiente, Aprobada, Ajustada y aprobada, Rechazada,
Cancelada; Enviada, Editada, Aprobada, Ajustada y aprobada, Rechazada, Cancelada.

## 5. Reglas de negocio

- Creación y edición técnica solo admiten `work_date` de la semana calendario lunes–domingo actual
  en `America/Panama`. Cancelar una solicitud pendiente anterior sí está permitido.
- Una jornada ocurre en un único día: `exit_time` debe ser posterior a `entry_time`; no cruza medianoche.
- Todos los horarios tienen precisión exacta de minutos; segundos o microsegundos distintos de cero
  se rechazan.
- El receso se envía completo o se omite; debe estar dentro de la jornada y tener duración positiva.
- El backend calcula y persiste `worked_minutes`, `regular_minutes` (máximo 480) y
  `overtime_minutes`. Mobile solo los lee.
- No se solapan intervalos del mismo técnico/compañía/fecha si están `pending`, `approved` o
  `adjusted`. `rejected` y `cancelled` liberan la franja. Intervalos adyacentes están permitidos.
- El técnico solo edita o cancela una solicitud propia `pending`. El PATCH puede cambiar fecha,
  horarios, actividad, proyecto y supervisor autorizante; todo se revalida como objeto final.
- Cambiar `authorizing_supervisor_id` cambia inmediatamente qué supervisor puede ver/revisar la
  solicitud cuando la transacción se confirma.
- El supervisor asignado solo revisa solicitudes `pending`. Ajustar y aprobar no cambia
  `work_date`, técnico, compañía ni supervisor autorizante.
- `404` oculta recursos fuera del alcance; `403` indica rol/usuario operativo inválido; `409` indica
  transición o intervalo incompatible; `422` indica forma/tipo inválido.
- Los endpoints `/page` y exportación permiten un máximo de 366 fechas inclusivas. Sin rango usan
  hoy en Panamá y los 30 días anteriores.
- Exportación PDF: máximo 2000 solicitudes. XLSX: máximo 10000.

## 6. Paginación y transición mobile

Los endpoints array con `skip`/`limit` permanecen compatibles y no están deprecados. Los nuevos
`/page` usan `page` desde 1 y `page_size` de 1 a 100, devuelven `total`, `total_pages` y el rango
efectivo. Una página fuera de rango responde `200` con `items=[]`.

Migración recomendada:

1. introducir tipos `OvertimeRequestPage` y filtros comunes en el servicio mobile;
2. mantener temporalmente el método array existente;
3. migrar hooks/pantallas a query keys que incluyan rol, página, tamaño, estado, fechas y técnico;
4. resetear `page=1` al cambiar filtros;
5. invalidar listas array y paginadas, además del detalle, tras crear, editar, cancelar o revisar;
6. retirar el consumo legacy solo después de validar la versión distribuida.

## 7. Exportaciones

Ruta única: `GET /api/overtime/supervisor/requests/export`. Acepta `format=pdf|xlsx`, `status`,
`technician_id`, `date_from` y `date_to`; no acepta parámetros de paginación ni IDs de compañía o
supervisor.

- PDF: `application/pdf`, filename `horas-extra_{date_from}_{date_to}.pdf`.
- XLSX: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, filename
  `horas-extra_{date_from}_{date_to}.xlsx`.
- Ambos: bytes directos y `Content-Disposition: attachment`.
- XLSX contiene `Solicitudes`, `Resumen por técnico` y `Resumen general`.
- Mobile debe descargar autenticado a almacenamiento temporal controlado, respetar el filename y
  MIME del response, y abrir/compartir mediante APIs compatibles con Expo. No convierta el body a JSON.

## 8. Slices propuestos para React Native

### Mobile 1 — Contrato y capa de datos (3–4 h)

Alcance: enums, tipos, schemas runtime si existen, servicio HTTP, filtros, query keys y métodos
legacy/nuevos. Fuera de alcance: UI y descarga. Criterios: serialización exacta, Bearer preservado,
`cancelled`/`edited` tolerados y ninguna pantalla rota. Pruebas: mappers, payloads, error parsing y
query keys. Dependencia: este handoff y backend local controlado.

### Mobile 2 — Edición y cancelación técnica (3–4 h)

Alcance: acción visible solo en `pending`, formulario precargado, PATCH parcial, retiro de receso,
confirmación de cancelación e invalidaciones. Fuera de alcance: paginación/exportación. Criterios:
errores 404/409/422 accionables y navegación coherente. Pruebas: validación de receso, payload diff,
doble toque/reintento y estados loading/error/success. Dependencia: Mobile 1.

### Mobile 3 — Filtros y paginación (3–4 h)

Alcance: migrar técnico y supervisor a `/page`, fechas, estado, técnico supervisor, navegación y
vacíos. Fuera de alcance: exportación. Criterios: rango efectivo visible o conservado en estado,
reset de página al filtrar y arrays legacy disponibles durante transición. Pruebas: query keys,
cambio de filtros, última página, página vacía y `cancelled`. Dependencias: Mobile 1; puede seguir a 2.

### Mobile 4 — Exportar, descargar y compartir (3–4 h)

Alcance: selector PDF/XLSX, filtros actuales, respuesta binaria, filename, almacenamiento temporal,
apertura/compartición y limpieza. Fuera de alcance: generación local. Criterios: MIME y extensión
correctos, 413 accionable, auth presente y archivos abribles. Pruebas: mocks binarios, headers,
permisos del dispositivo y cancelación de descarga. Dependencias: Mobile 1 y filtros de Mobile 3.

### Mobile 5 — Validación integrada (3–4 h)

Alcance: matriz manual de la sección siguiente, Expo/dispositivos objetivo y correcciones puntuales.
Fuera de alcance: nuevas capacidades. Criterios: evidencia por rol, regresión legacy y decisión de
integración/despliegue. Pruebas: smoke E2E controlado y casos de concurrencia/reintento. Dependencias:
Mobile 2–4 y backend disponible en entorno controlado.

## 9. Matriz de validación manual pendiente

### Técnico

- Crear con/sin receso; comprobar minutos y evento `submitted`.
- Editar cada campo y combinaciones; retirar receso; cambiar supervisor.
- Cancelar pendiente, cancelar antigua y repetir cancelación.
- Ver estados/eventos nuevos y errores de semana, horario y solapamiento.

### Supervisor

- Ver únicamente asignadas; aprobar, ajustar/aprobar y rechazar.
- Confirmar que un cambio de supervisor mueve la visibilidad.
- Intentar segunda resolución y revisar notas/historial.

### Permisos y aislamiento

- Técnico/supervisor de otra compañía obtiene lista vacía o `404` según operación.
- Técnico no usa rutas supervisor y supervisor no usa rutas técnico.
- IDs de técnico en filtros nunca amplían visibilidad.

### Concurrencia y reintentos

- Dos creaciones solapadas simultáneas: una confirma y otra recibe conflicto.
- Cancelar frente a aprobar y editar frente a cancelar: un estado final y eventos coherentes.
- Doble toque/reintento de mutaciones muestra el `409` sin duplicar optimismo local.

### Paginación y filtros

- Rango default, un solo límite, 366 permitido y 367 rechazado.
- Estados incluido `cancelled`, técnico supervisor, cambio de página y resultado vacío.
- Comparar temporalmente resultados array y `/page` para el mismo filtro.

### PDF/XLSX

- Descargar ambos formatos con filtros y resultado vacío.
- Validar filename, MIME, apertura, Unicode, duraciones mayores de 24 horas y tres hojas XLSX.
- Confirmar 413 específico por formato y limpieza de temporales mobile.

### Regresión de primera iteración

- Catálogos, creación, arrays legacy, detalle y tres acciones supervisor existentes.
- Navegación, badges y parsing no fallan al aparecer enums nuevos.

## 10. Secuencia coordinada de integración

1. Cerrar y guardar backend en la rama siguiendo la autorización del desarrollador.
2. Implementar mobile contra este contrato consolidado.
3. Validar mobile con backend local o entorno controlado, nunca suponiendo producción actualizada.
4. Autorizar commit/merge según el flujo del desarrollador.
5. Desplegar migraciones y backend de forma coordinada con rollback preparado.
6. Ejecutar smoke tests backend/mobile en el entorno desplegado.
7. Distribuir y validar la versión mobile compatible.
8. Corregir únicamente hallazgos puntuales y volver a validar.

Este documento no autoriza commits, merges, migraciones remotas, deploy ni distribución mobile.
