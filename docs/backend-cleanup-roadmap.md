# VertiOne Backend Cleanup Roadmap

Roadmap para limpiar el backend sin romper la app mobile actual. La regla base es preservar contrato primero, observar segundo y modificar despues.

## Principios

- No eliminar endpoints durante las fases 1 a 4.
- No cambiar payloads, rutas, codigos de respuesta ni nombres de roles durante estabilizacion.
- No modificar migraciones ni base de datos como parte de la limpieza documental.
- No mover ownership de servicios legacy a servicios nuevos sin smoke tests.
- Toda deprecacion debe tener medicion de uso, alternativa y ventana de compatibilidad.

## Fase 1: observabilidad

Objetivo: saber que endpoints usa mobile y con que roles antes de tocar comportamiento.

Acciones:

- Agregar logging/metricas por metodo, path normalizado, status code, rol, company_id anonimo y version de app si llega en headers.
- Separar dashboards de uso para endpoints protegidos, publicos y legacy.
- Medir uso de rutas duplicadas/shadowed en `usuarios.py`, especialmente `/api/usuarios/{uid}`, `/count`, `/all`, `/clients/*`, `/by-role/*` y `/by-company/*`.
- Medir uso de endpoints publicos operativos antes de agregar auth.
- Medir latencia y errores de WeasyPrint/reportes.

Entregable esperado:

- Reporte de uso por endpoint durante una ventana representativa.
- Lista de endpoints con uso mobile confirmado.
- Lista de endpoints sin uso observado, todavia sin eliminar.
- Guia de lectura de logs en `docs/observability.md`.

No hacer en esta fase:

- No cambiar auth.
- No reordenar rutas.
- No renombrar roles.
- No tocar payloads.

## Fase 2: seguridad/auth

Objetivo: reducir exposicion sin cortar clientes existentes.

Acciones:

- Clasificar endpoints publicos entre catalogos de lectura, mutaciones administrativas, datos operativos y reportes.
- Definir politica compatible para endpoints publicos: mantener temporalmente, crear alternativa protegida o activar auth con feature flag/version gate.
- Auditar filtros multiempresa por endpoint operativo.
- Documentar mapa de roles actual y aliases legacy (`superAdmin`, `super_admin`, `technician`, `tecnico`, `client`, `cliente`, `operativo`).
- Preparar normalizacion de roles solo con adaptadores, no con renombre directo.

Entregable esperado:

- Matriz endpoint -> auth actual -> auth objetivo -> riesgo -> plan de compatibilidad.
- Tests de permisos para rutas criticas antes de cambiar guards.

No hacer en esta fase:

- No eliminar aliases de roles.
- No cerrar endpoints publicos sin confirmar mobile/consumidores.

## Fase 3: pruebas smoke API

Objetivo: crear red de seguridad para limpiar sin romper contratos.

Acciones:

- Agregar smoke tests para los 137 endpoints registrados.
- Validar que cada ruta exista con metodo esperado.
- Validar rutas shadowed de `usuarios.py` antes de cualquier reordenamiento.
- Agregar fixtures minimos para checklists y sync offline usando payloads existentes en `docs/checklist*.json` cuando aplique.
- Cubrir grupos criticos: usuarios, ordenes-trabajo, seguimiento, checklists, clientes, proyectos, unidades, dashboards y LOV.
- Fijar response shape minima sin exigir datos productivos.

Entregable esperado:

- Suite `tests/test_api` o equivalente.
- Pruebas de contrato para rutas protegidas mobile.
- Pruebas que fallen si se elimina/renombra una ruta protegida.

No hacer en esta fase:

- No usar los tests como excusa para cambiar contratos existentes.

## Fase 4: optimizacion performance

Objetivo: mejorar latencia/costo manteniendo exactamente los mismos contratos.

Acciones:

- Eliminar N+1 en listados de ordenes con eager loading/joins para estados.
- Eliminar N+1/N+3 en `/api/unidades/company/all` reemplazando `_map_unidad` por consulta con relaciones cargadas.
- Reemplazar filtros mensuales con `extract(year/month, ...)` por rangos de fechas cuando sea compatible con indices.
- Revisar streams completos de Firestore para conteos/listados y migrar a cursores/agregaciones si no cambia shape.
- Lazy import de WeasyPrint/Jinja2/storage dentro de rutas o tareas PDF.
- Verificar que startup no cargue dependencias pesadas innecesarias.

Entregable esperado:

- Mismas rutas y payloads con menor latencia.
- Pruebas smoke pasando antes y despues.
- Nota de performance por endpoint optimizado.

No hacer en esta fase:

- No cambiar nombres de campos.
- No cambiar estructura de paginacion.

## Fase 5: deprecacion controlada

Objetivo: retirar deuda solo cuando haya evidencia y alternativa.

Acciones:

- Marcar endpoints legacy con `deprecated=True` en OpenAPI solo despues de confirmar plan.
- Publicar tabla de reemplazo: endpoint legacy -> endpoint nuevo -> diferencia de contrato -> fecha objetivo.
- Mantener compatibilidad durante al menos una version mobile estable.
- Para `usuarios.py`, planear reordenamiento o rutas nuevas sin romper `/api/usuarios/{uid}` existente.
- Para ordenes/unidades, decidir ownership definitivo antes de migrar routers.
- Remover codigo legacy solo tras telemetria sin uso y aprobacion explicita.

Entregable esperado:

- Changelog interno de deprecacion.
- Versionado o compatibilidad documentada.
- Lista de endpoints candidatos a retiro con evidencia.

No hacer en esta fase:

- No eliminar endpoints por intuicion.
- No cambiar servicios activos por servicios nuevos incompletos.

## Fase 6: endpoints web

Objetivo: separar necesidades web/admin futuras sin contaminar contrato mobile.

Acciones:

- Crear endpoints web nuevos con prefijo o version clara si necesitan payload distinto.
- Mantener mobile contract intacto.
- Para dashboards web, preferir agregados especificos web antes que modificar dashboards mobile.
- Para administracion web, usar auth/roles canonicos y response models nuevos.
- Documentar diferencias entre contrato mobile y web.

Entregable esperado:

- Superficie web separada o versionada.
- Contratos Pydantic dedicados cuando web necesite campos distintos.
- Pruebas de no regresion para mobile.

## Orden recomendado

1. Congelar contrato con `docs/backend-mobile-contract.md`.
2. Instrumentar y medir.
3. Crear smoke tests.
4. Corregir seguridad con compatibilidad.
5. Optimizar queries/imports.
6. Deprecar con evidencia.
7. Agregar endpoints web separados.

## Definition of done para limpieza segura

- Mobile actual sigue funcionando con las mismas rutas y payloads.
- Smoke tests cubren endpoints protegidos.
- Riesgos criticos tienen mitigacion o plan aceptado.
- Endpoints legacy estan documentados antes de ser tocados.
- No hay cambios de base de datos ni migraciones no requeridas.
