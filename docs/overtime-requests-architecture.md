# Arquitectura de solicitudes de horas extra

## Objetivo y alcance

El dominio permite que un técnico registre una jornada real con horas extra y que el supervisor seleccionado la resuelva. Incluye persistencia, cálculo/validación pura, API protegida, servicio de dominio y auditoría transaccional.

No se implementan integración móvil, notificaciones, control de asistencia, entrada/salida diaria, GPS, geocercas, marcaciones, fichaje ni cálculo legal de jornada.

## Separación del dominio

Una solicitud de horas extra es una declaración y flujo de aprobación. No es una marcación de asistencia. Se mantiene separada conceptual y técnicamente del futuro módulo de asistencia/GPS para que este último pueda manejar eventos, precisión geográfica y reglas laborales sin alterar el historial de solicitudes.

## Entidades y relaciones

`overtime_requests` conserva el estado vigente. Usa UUID y referencia las tablas reales:

- `company_id -> companias.id`: frontera multiempresa.
- `technician_id -> usuarios.id`: técnico solicitante.
- `project_id -> proyectos.id`: proyecto asociado.
- `authorizing_supervisor_id -> usuarios.id`: supervisor elegido manualmente.
- `reviewed_by_user_id -> usuarios.id`: usuario que materializó una revisión, nullable.

`overtime_request_events` conserva la auditoría inmutable y referencia la solicitud, compañía y usuario actor. Sus snapshots son `JSONB`, adecuado al PostgreSQL ya usado por el proyecto. El servicio inserta eventos y no los actualiza ni elimina. No hay cascada de eliminación: no existe eliminación física de solicitudes y una FK impide borrar una solicitud con historia.

La base no puede probar por sí sola que técnico, proyecto y supervisor pertenecen a la misma compañía sin triggers o claves compuestas invasivas. El servicio transaccional realiza esa validación y los repositorios filtran por `company_id`.

## Estados y auditoría

Estados persistidos en minúsculas mediante enum PostgreSQL `overtime_request_status`:

- `pending`: enviada y pendiente de revisión.
- `approved`: aprobada sin ajustes.
- `adjusted`: modificada y aprobada.
- `rejected`: rechazada.
- `cancelled`: cancelada por el técnico mientras estaba pendiente.

Eventos mediante `overtime_request_event_type`: `submitted`, `edited`, `cancelled`, `approved`, `adjusted_and_approved` y `rejected`. `edited` conserva `pending → pending`; `cancelled` conserva `pending → cancelled`. Ambos registran actor técnico y snapshots anterior/posterior sin modificar ni eliminar eventos previos.

Solo `authorizing_supervisor_id`, el supervisor seleccionado por el técnico y perteneciente a su compañía, puede revisar la solicitud. La capa HTTP y el servicio comprueban conjuntamente rol, compañía, identidad del supervisor y estado permitido. `reviewed_by_user_id` aporta evidencia, pero no sustituye esa autorización.

## Contrato preliminar de datos

La solicitud contiene `id`, `company_id`, `technician_id`, `work_date`, `entry_time`, receso opcional como par, `exit_time`, `activity`, `project_id`, `authorizing_supervisor_id`, los tres totales en minutos enteros, `status`, fechas de envío/revisión/creación/actualización, revisor y nota opcionales.

El evento contiene `id`, `overtime_request_id`, `company_id`, `actor_user_id`, `event_type`, estados anterior/nuevo, nota, snapshots y `created_at`. Este contrato es de persistencia preliminar; no constituye un payload público ni promete nombres/formatos HTTP.

## Reglas puras de horario y cálculo

La jornada ocurre en un único `work_date`. `exit_time` debe ser estrictamente posterior a `entry_time`; por ello no se permiten jornadas que crucen medianoche. Con campos `time` y una sola fecha, una salida menor representa tanto un orden inválido como un intento de cruce de medianoche y se rechaza con el mismo error accionable.

El receso se informa completo o se omite. Debe comenzar dentro de la jornada, terminar después de comenzar y no superar la salida. Los horarios nominales 07:00, 12:00–12:30 y 15:30 son referencias operativas, no restricciones. Todos los horarios se aceptan con precisión exacta de minutos; cualquier valor con segundos o microsegundos es inválido y se rechaza antes del cálculo.

Todos los cálculos y la persistencia usan minutos enteros:

```text
worked_minutes = exit - entry - break
regular_minutes = min(worked_minutes, 480)
overtime_minutes = max(worked_minutes - 480, 0)
```

La tabla refuerza que el trabajo sea positivo, los regulares estén entre 0 y 480, las extras no sean negativas y ambos componentes sumen el total. El backend es la fuente de verdad; los clientes no pueden imponer los totales calculados.

## Semana y zona horaria

La ventana lunes-domingo de la semana calendario actual en `America/Panama` limita el envío inicial y el resultado final de una edición técnica. Una solicitud pendiente de una semana anterior puede cancelarse, pero no editarse.

La revisión del supervisor puede realizarse en semanas posteriores. Al corregir y aprobar se revalidan los intervalos horarios, el receso y la precisión de minutos, y se recalculan `worked_minutes`, `regular_minutes` y `overtime_minutes`; no se vuelve a validar que `work_date` pertenezca a la semana actual.

La función recibe `now` explícitamente. Los `datetime` conscientes se convierten a Panamá; uno naive se interpreta como hora de Panamá. Un `date` se usa como fecha de Panamá.

## Integridad de intervalos activos

Un técnico no puede tener jornadas activas solapadas dentro de la misma compañía y fecha. Bloquean los estados `pending`, `approved` y `adjusted`; `rejected` y `cancelled` no bloquean. El intervalo protegido es toda la jornada entre `entry_time` y `exit_time`: el receso no lo divide.

La intersección usa `existing.entry_time < new.exit_time AND existing.exit_time > new.entry_time`. Por tanto, los intervalos son semiabiertos `[)` y se permiten franjas adyacentes, como `08:00–10:00` y `10:00–12:00`.

La creación hace primero una consulta de existencia, aislada por `company_id`, `technician_id` y `work_date`, para devolver un `409` accionable. La garantía concurrente definitiva es la restricción GiST parcial `excl_overtime_requests_active_overlap`, que combina igualdad de compañía y técnico mediante `btree_gist` con intersección de `tsrange(work_date + entry_time, work_date + exit_time, '[)')`.

Si dos transacciones superan simultáneamente la validación previa, PostgreSQL solo permite confirmar una. El servicio traduce exclusivamente la violación cuyo `constraint_name` coincide con la restricción anterior al mismo `409`; otros `IntegrityError` se propagan. No usa la sesión después del `flush` fallido: `get_db` ejecuta el rollback de toda la unidad transaccional.

La migración `c4f8a1d2e6b9` detecta primero datos activos ya solapados y falla explícitamente sin corregirlos. Habilita `btree_gist` si hace falta y el downgrade elimina solo la restricción, no la extensión compartida.

## Índices y restricciones

Hay índices simples para compañía, técnico, supervisor autorizante, fecha, estado y envío. Los índices compuestos cubren `company_id + status`, `technician_id + work_date` y `authorizing_supervisor_id + status`. No existe unicidad por técnico/fecha: futuras versiones pueden admitir varias actividades o intervalos el mismo día.

## Riesgos y siguientes fases

- Adoptar el contrato consolidado y validar los flujos manuales desde el repositorio React Native.
- Evaluar idempotencia explícita para reintentos offline antes de introducir colas de mutaciones mobile.
- Impedir mutaciones/borrados de eventos también a nivel de permisos de base de datos si el despliegue lo requiere.
- Evaluar políticas de retención, privacidad y reporting.

## Contrato API

Todos los endpoints usan Bearer token Firebase y el prefijo `/api/overtime`. El servicio resuelve el usuario PostgreSQL por el `uid` autenticado y usa su UUID y `company_id`; no confía en identidad o compañía enviadas por el cliente.

| Método | Endpoint | Rol | Descripción |
| --- | --- | --- | --- |
| GET | `/catalogs/projects` | `technician` | Proyectos activos de su compañía; devuelve solo `id`, `name`. |
| GET | `/catalogs/supervisors` | `technician` | Supervisores activos de su compañía; devuelve solo `id`, `name`. |
| POST | `/requests` | `technician` | Crea para sí mismo y genera `submitted`. |
| GET | `/requests/me` | `technician` | Lista propia con filtros `status`, `date_from`, `date_to`, `skip`, `limit`. |
| GET | `/requests/me/page` | `technician` | Lista propia paginada con rango efectivo y metadatos. |
| GET | `/requests/me/{request_id}` | `technician` | Detalle propio e historial ascendente. |
| PATCH | `/requests/me/{request_id}` | `technician` | Edita parcialmente una solicitud propia pendiente y genera `edited`. |
| POST | `/requests/me/{request_id}/cancel` | `technician` | Cancela una solicitud propia pendiente y genera `cancelled`. |
| GET | `/supervisor/requests` | `supervisor` | Lista solo asignadas; acepta además `technician_id`. |
| GET | `/supervisor/requests/page` | `supervisor` | Lista asignada paginada; acepta filtro opcional de técnico. |
| GET | `/supervisor/requests/export?format=pdf|xlsx` | `supervisor` | Descarga PDF o XLSX de todo el resultado autorizado y filtrado. |
| GET | `/supervisor/requests/{request_id}` | `supervisor` | Detalle solo si fue el supervisor elegido. |
| POST | `/supervisor/requests/{request_id}/approve` | `supervisor` | Aprueba; `note` opcional. |
| POST | `/supervisor/requests/{request_id}/adjust-and-approve` | `supervisor` | Corrige todos los valores finales y aprueba. |
| POST | `/supervisor/requests/{request_id}/reject` | `supervisor` | Rechaza con `note` obligatoria. |

La creación acepta `work_date`, los cuatro horarios (receso nullable como par), `activity`, `project_id` y `authorizing_supervisor_id`. Prohíbe campos de identidad, compañía, estado, revisión y minutos calculados. Devuelve `201` con el detalle. El ajuste exige el conjunto completo de valores finales (`entry_time`, ambos campos de receso, `exit_time`, `activity`, `project_id`, `note`); no permite cambiar fecha, técnico, compañía ni supervisor autorizante, y puede ejecutarse en una semana posterior a la fecha trabajada.

El PATCH técnico permite `work_date`, horarios, actividad, proyecto y supervisor autorizante. Usa `model_fields_set` para distinguir campos omitidos de `null`: solo ambos extremos del receso admiten `null`, permitiendo retirarlo. Un payload vacío devuelve `422`. El servicio combina el PATCH con la fila bloqueada, valida el objeto final completo, vuelve a validar semana/proyecto/supervisor/solapamientos, recalcula minutos y conserva `submitted_at`/`created_at`. Identidad, estado, revisión, minutos calculados, timestamps y eventos son inmutables desde el payload.

La cancelación no recibe payload, no elimina la fila ni establece campos de revisión. Solo realiza `pending → cancelled`, actualiza `updated_at` y agrega el evento correspondiente. Un segundo intento devuelve `409`.

Las respuestas resumidas incluyen jornada, proyecto, técnico, supervisor, minutos, estado y fechas principales. El detalle agrega horarios, nota, timestamps e historial. Horas se serializan como `HH:MM`, UUID como string, enums por valor y fechas ISO.

## Errores y visibilidad

- `400`: jornada, rango o selección de proyecto/supervisor inválidos.
- `401`: token ausente o inválido.
- `403`: rol o usuario PostgreSQL activo no permitido.
- `404`: solicitud no visible; no revela existencia fuera de técnico, compañía o supervisor asignado.
- `409`: solicitud ya no pendiente o creación/edición solapada con una jornada activa del técnico.
- `422`: forma/tipo del payload, campos extra, nota vacía o precisión horaria inválida detectada por Pydantic.

Los listados usan `skip` desde 0 y `limit` entre 1 y 100 (default 20). Técnico: `work_date DESC, submitted_at DESC`. Supervisor: pendientes primero y luego el mismo orden descendente.

## Listados paginados y transición mobile

Los endpoints array anteriores permanecen intactos para mobile de primera iteración. La nueva superficie `/page` usa `page` desde 1 y `page_size` entre 1 y 100 (default 20), un único `status`, `date_from` y `date_to`; supervisor acepta además `technician_id` dentro de sus solicitudes asignadas.

Sin fechas, el servicio deriva en `America/Panama` una ventana inclusiva de 31 fechas (`hoy - 30 días` hasta hoy). Con un solo límite completa 30 días hacia el otro extremo. El máximo permitido es 366 fechas inclusivas; rangos invertidos o de 367 días devuelven `400`. Los límites efectivos siempre aparecen en la respuesta.

La respuesta contiene `items`, `page`, `page_size`, `total`, `total_pages`, `date_from` y `date_to`. Una página posterior a la última devuelve `200` con `items=[]`; si no hay resultados, `total_pages=0`.

Repositorio ejecuta un `COUNT(*)` y una consulta limitada con los mismos predicados, sin cargar todos los registros. Técnico ordena `work_date DESC, submitted_at DESC, id DESC`. Supervisor coloca `pending` primero y luego usa el mismo orden estable; `cancelled` pertenece al grupo no pendiente.

La identidad y compañía siempre proceden del usuario autenticado. Técnico solo ve registros propios; supervisor solo los de su compañía asignados mediante `authorizing_supervisor_id`, incluso al filtrar por técnico. Mobile actual puede continuar con arrays mientras la segunda iteración migra a `/page`; una retirada futura exige medición y versión mobile coordinada.

## Exportación PDF y XLSX de supervisor

`GET /api/overtime/supervisor/requests/export?format=pdf` devuelve bytes `application/pdf` como attachment `horas-extra_{date_from}_{date_to}.pdf`. Acepta el mismo rango efectivo, estado único y filtro opcional de técnico del listado paginado, pero no acepta paginación y representa todo el resultado autorizado.

El repositorio reutiliza los predicados de compañía, supervisor asignado, técnico, estado y fechas. Primero ejecuta `COUNT(*)`; si supera 2000 solicitudes, el servicio devuelve `413` sin consultar filas ni renderizar. Con cero filas devuelve un PDF válido con contexto, mensaje vacío y total general cero. El orden deliberado del reporte es técnico ascendente, fecha ascendente, entrada ascendente e ID ascendente.

El contexto incluye técnico, proyecto, fecha, horario, receso, actividad, minutos persistidos, etiqueta de estado, totales por técnico y total general. Los minutos se presentan como `HH:MM`, incluido `00:00` y duraciones mayores de 24 horas. Rechazadas y canceladas participan en totales cuando están dentro del filtro: son totales de solicitudes, no una obligación de pago.

Un renderer propio del dominio carga una plantilla local Jinja2 con autoescape y convierte HTML a bytes mediante WeasyPrint. No usa archivos temporales, red, imágenes remotas ni `|safe`. La plantilla A4 horizontal mantiene presentación y cortes de página sin contener reglas de negocio.

El mismo endpoint admite `format=xlsx` y devuelve bytes `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` como attachment `horas-extra_{date_from}_{date_to}.xlsx`. El servicio comparte autorización, rango, filtros, consulta y contexto/totales con PDF; selecciona un límite independiente de 10000 solicitudes y devuelve `413` antes de cargar filas o renderizar cuando se excede. PDF conserva su límite de 2000.

`OvertimeXlsxRenderer`, basado en la dependencia directa `openpyxl`, genera en memoria las hojas `Solicitudes`, `Resumen por técnico` y `Resumen general`. Fechas y horarios son valores nativos de Excel; las duraciones son valores numéricos con formato `[h]:mm`. Los totales usan los minutos persistidos calculados por backend, no fórmulas, e incluyen cualquier estado filtrado: representan solicitudes y no una nómina pagable. El resultado vacío mantiene las tres hojas, encabezados y totales cero. Todo texto de compañía, técnico, proyecto, actividad o filtros cuyo primer carácter no blanco sea `=`, `+`, `-` o `@` recibe un apóstrofo protector para impedir inyección de fórmulas.

## Transacciones, bloqueo y snapshots

Repositorio y servicio solo hacen `flush`; no hacen commit. `get_db` realiza un único commit al final o rollback ante cualquier excepción. Así, la solicitud/transición y su evento se confirman juntas. Edición, cancelación y revisión recuperan la fila visible con `SELECT ... FOR UPDATE` y vuelven a comprobar `pending` después del lock. Esto serializa carreras sobre una misma solicitud; la restricción GiST sigue protegiendo carreras entre solicitudes distintas.

Una única función serializa snapshots JSONB con UUID string, fecha/datetime ISO, hora `HH:MM` y enum por valor. `submitted` guarda solo snapshot posterior; las resoluciones guardan antes y después. Los eventos no tienen endpoints de modificación ni eliminación.

## Fuera de alcance actual

React Native, reapertura, eliminación física, delegación, notificaciones, asistencia/GPS y jornadas nocturnas siguen fuera de alcance.

## Estado operativo

La segunda iteración backend está integrada en `main` y desplegada. Según la evidencia suministrada
por el desarrollador, las migraciones `c4f8a1d2e6b9` y `e7a3c9d4f2b1` están aplicadas en producción,
cuya revisión efectiva es `e7a3c9d4f2b1 (head)`. Los consumidores React Native pueden adoptar y
validar este contrato desde su repositorio independiente.
