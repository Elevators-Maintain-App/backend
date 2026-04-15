---
name: checklist-contract-sync
description: Usa esta skill cuando el cambio afecte el contrato de checklists, evidencias, sincronización desde mobile, reportes PDF o validaciones de cierre de orden.
---

# Checklist Contract Sync

## Objetivo
Proteger el punto de integración más delicado entre la app móvil y el backend: el envío, validación y persistencia de checklists con evidencias.

## Dónde mirar primero
- `app/api/routes/checklists.py`
- `app/services/checklists.py`
- `app/schemas/checklists.py`
- `app/schemas/checklists_sync.py`
- modelos y repositorios relacionados con checklist/evidencias/seguimiento
- plantillas de reporte en `app/templates/*`

## Principios
1. El mobile puede reenviar por reintento; el backend debe comportarse de forma segura ante duplicados cuando el flujo lo requiera.
2. El contrato debe aceptar el estado real del trabajo offline: evidencias locales primero, URLs remotas después.
3. Las validaciones deben ser estrictas en integridad pero claras en mensaje.
4. Cambios en checklist pueden afectar reportes y dashboards, no solo el endpoint.

## Procedimiento recomendado
1. Revisa el schema actual de submit y la forma en que mobile lo construye.
2. Si agregas campos, intenta que sean backward compatible.
3. Si haces obligatorios nuevos campos, documenta el impacto y provee mensaje de error útil.
4. Revisa persistencia de evidencias multimedia y referencias a orden/paso.
5. Revisa generación de PDF o vistas derivadas si el checklist alimenta reportes.

## Validaciones mínimas
- Submit válido de checklist completo.
- Manejo de evidencias con URL remota.
- Respuesta comprensible ante payload incompleto.
- No duplicar registros funcionales por reintentos razonables.
- Compatibilidad con filtros posteriores de seguimiento/reportes.

## Qué evitar
- Cambiar el contrato por conveniencia del backend ignorando la app móvil.
- Mezclar lógica de generación de reporte dentro del endpoint.
- Romper compatibilidad de campos sin plan de migración.

## Resultado esperado
Un flujo de checklist robusto y coordinado entre mobile, persistencia y salidas derivadas.
