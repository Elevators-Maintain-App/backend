# frontend-backend-contract-alignment

## Cuándo usar esta skill
Usa esta skill cuando un cambio toque simultáneamente frontend mobile y backend, o cuando exista riesgo de desalineación entre payloads, nombres de campos, validaciones, estados, errores o flujos de sincronización.

Casos típicos:
- agregar o renombrar campos en requests/responses
- cambiar estructura de payload de checklist, órdenes, usuarios, proyectos o reportes
- ajustar validaciones de backend que impactan formularios mobile
- cambiar estados de negocio consumidos por la app
- modificar paginación, filtros o shape de listados
- corregir bugs donde el problema puede estar en el contrato y no en una sola capa

## Objetivo
Mantener un contrato explícito, estable y verificable entre app y API, minimizando regresiones silenciosas.

## Principios
1. Un cambio de contrato nunca debe implementarse “solo” en frontend o “solo” en backend si impacta a la otra parte.
2. El backend define el contrato fuente; el frontend adapta consumo de forma centralizada en services/hooks, no dispersa en pantallas.
3. Si el contrato debe cambiar, actualiza primero tipos y schemas, luego lógica, luego UI.
4. Evita renombrar campos existentes sin necesidad real. Prefiere compatibilidad hacia atrás durante la transición.
5. Los errores que el backend expone deben ser útiles para la UI y para debugging.
6. En flujos offline, el contrato debe soportar reintentos idempotentes o al menos errores recuperables.

## Procedimiento recomendado

### 1) Delimitar el contrato afectado
Antes de editar código, documenta mentalmente o en comentario corto:
- endpoint(s) afectados
- método HTTP
- request body / query params / path params
- response body
- reglas de validación
- roles involucrados
- pantallas, hooks y servicios mobile impactados

### 2) Revisar primero el backend
Ubica y revisa:
- `app/api/routes/*`
- `app/services/*`
- `app/db/repositories/*` si cambia persistencia
- `app/schemas/*`

Pregunta obligatoria: ¿el cambio es realmente de negocio o solo de presentación?
- Si es de presentación, resuélvelo en frontend.
- Si es de negocio/validación/persistencia, resuélvelo en backend y luego alinea frontend.

### 3) Revisar luego el frontend
Ubica y revisa:
- `src/services/*`
- `src/hooks/queries/*` o `src/hooks/mutations/*`
- `src/constants/query-keys.ts`
- `src/types/*` o tipos cercanos al dominio
- pantallas/formularios que muestran o envían esos datos

La transformación entre backend y UI debe centralizarse en `src/services/*` o en hooks, no en componentes presentacionales.

### 4) Ejecutar cambios en este orden
1. Backend schemas
2. Backend service/repository/route
3. Frontend types
4. Frontend service HTTP
5. Frontend query/mutation + invalidaciones
6. Pantallas/formularios/estados visuales
7. Manejo de error y empty states

### 5) Manejo de compatibilidad
Cuando sea posible:
- acepta temporalmente ambos nombres de campo en backend durante migraciones cortas
- mantén responses backward-compatible mientras frontend se actualiza
- evita eliminar campos si la app todavía puede leerlos

Si no es posible compatibilidad, deja el cambio completamente sincronizado en el mismo lote de trabajo.

## Reglas específicas para VertiOne
- Bearer token Firebase sigue siendo obligatorio en endpoints protegidos.
- No romper filtros por compañía, rol ni permisos por supervisor/técnico/admin.
- Un cambio en checklists puede impactar submit mobile, cola offline, sync worker, reportes PDF y dashboards.
- Si cambia un enum/estado, revisar navegación, badges, filtros, reportes y listados.
- Si cambia una fecha, coordenada, firma, evidencia o URL de archivo, verificar serialización completa de ida y vuelta.

## Qué revisar antes de dar por terminado el cambio
- ¿Los schemas backend y tipos frontend coinciden?
- ¿Los nombres de campo coinciden exactamente?
- ¿Los nullables/opcionales coinciden?
- ¿La UI entiende correctamente errores 400/401/403/404/409/422?
- ¿Las query keys o invalidaciones quedaron actualizadas?
- ¿Los flujos offline siguen pudiendo reintentar?
- ¿El cambio afecta reportes o dashboards además del flujo principal?

## Patrón de respuesta esperado para cambios de contrato
Al cerrar una tarea, deja constancia breve de:
- contrato afectado
- archivos backend tocados
- archivos frontend tocados
- riesgo residual
- validaciones manuales recomendadas

## Anti-patrones
- corregir “rápido” en pantalla un campo mal nombrado del backend
- duplicar mapeos de payload en varias pantallas
- devolver estructuras inconsistentes desde endpoints similares
- meter lógica de permisos en el frontend como sustituto del backend
- cambiar enums o estados sin revisar impacto transversal
- ocultar errores del backend con mensajes genéricos que impiden diagnosticar
