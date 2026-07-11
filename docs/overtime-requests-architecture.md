# Arquitectura de solicitudes de horas extra

## Objetivo y alcance

Esta fase establece la base documental, de persistencia y de lógica pura para que un técnico registre una jornada real con horas extra. Incluye los modelos `overtime_requests` y `overtime_request_events`, una migración Alembic, cálculo/validación sin infraestructura y pruebas unitarias.

No existen endpoints, schemas HTTP, repositorios, integración móvil ni cambios de contratos API en esta fase. Tampoco se implementan revisión, notificaciones, control de asistencia, entrada/salida diaria, GPS, geocercas, marcaciones, fichaje ni cálculo legal de jornada.

## Separación del dominio

Una solicitud de horas extra es una declaración y flujo de aprobación. No es una marcación de asistencia. Se mantiene separada conceptual y técnicamente del futuro módulo de asistencia/GPS para que este último pueda manejar eventos, precisión geográfica y reglas laborales sin alterar el historial de solicitudes.

## Entidades y relaciones

`overtime_requests` conserva el estado vigente. Usa UUID y referencia las tablas reales:

- `company_id -> companias.id`: frontera multiempresa.
- `technician_id -> usuarios.id`: técnico solicitante.
- `project_id -> proyectos.id`: proyecto asociado.
- `authorizing_supervisor_id -> usuarios.id`: supervisor elegido manualmente.
- `reviewed_by_user_id -> usuarios.id`: usuario que materializó una revisión, nullable.

`overtime_request_events` conserva la auditoría inmutable y referencia la solicitud, compañía y usuario actor. Sus snapshots son `JSONB`, adecuado al PostgreSQL ya usado por el proyecto. La aplicación futura deberá insertar eventos y nunca actualizarlos ni eliminarlos. No hay cascada de eliminación: no existe eliminación física de solicitudes y una FK impide borrar una solicitud con historia.

La base no puede probar por sí sola que técnico, proyecto y supervisor pertenecen a la misma compañía sin triggers o claves compuestas invasivas. Esa validación será obligatoria en el futuro servicio transaccional, siempre filtrando por `company_id`.

## Estados y auditoría

Estados persistidos en minúsculas mediante enum PostgreSQL `overtime_request_status`:

- `pending`: enviada y pendiente de revisión.
- `approved`: aprobada sin ajustes.
- `adjusted`: modificada y aprobada.
- `rejected`: rechazada.

Eventos iniciales mediante `overtime_request_event_type`: `submitted`, `approved`, `adjusted_and_approved` y `rejected`. Cada transición futura debe guardar estado anterior (nullable para el envío), estado nuevo, actor, nota y snapshot posterior; el snapshot anterior es nullable para el evento inicial.

Solo `authorizing_supervisor_id`, el supervisor seleccionado por el técnico y perteneciente a su compañía, podrá revisar la solicitud. Una fase HTTP futura deberá comprobar conjuntamente rol, compañía, identidad del supervisor y estado permitido. `reviewed_by_user_id` aporta evidencia, pero no sustituye esa autorización.

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

La tabla refuerza que el trabajo sea positivo, los regulares estén entre 0 y 480, las extras no sean negativas y ambos componentes sumen el total. El backend será la fuente de verdad; futuros clientes no podrán imponer los totales calculados.

## Semana y zona horaria

Solo se acepta una fecha entre lunes y domingo de la semana calendario actual en `America/Panama`. El domingo aún acepta cualquier fecha desde el lunes anterior; a las 00:00 del lunes de Panamá empieza una semana nueva. La función recibe `now` explícitamente. Los `datetime` conscientes se convierten a Panamá; uno naive se interpreta como hora de Panamá. Un `date` se usa como fecha de Panamá.

## Índices y restricciones

Hay índices simples para compañía, técnico, supervisor autorizante, fecha, estado y envío. Los índices compuestos cubren `company_id + status`, `technician_id + work_date` y `authorizing_supervisor_id + status`. No existe unicidad por técnico/fecha: futuras versiones pueden admitir varias actividades o intervalos el mismo día.

## Riesgos y siguientes fases

- Implementar un servicio transaccional que valide roles y pertenencia multiempresa de técnico, supervisor y proyecto.
- Definir transiciones permitidas e insertar solicitud más evento `submitted` atómicamente.
- Impedir mutaciones/borrados de eventos también a nivel de permisos de base de datos si el despliegue lo requiere.
- Decidir concurrencia de revisión (bloqueo o control optimista) e idempotencia para reintentos móviles.
- Diseñar schemas/endpoints sin aceptar totales calculados como fuente autoritativa.
- Acordar cómo representar correcciones en snapshots y conservar la solicitud original.
- Evaluar políticas de retención, privacidad y reporting.
- Integrar más adelante con mobile offline sin mezclar este dominio con asistencia/GPS.

Confirmación: esta fase no registra routers ni crea endpoints.
