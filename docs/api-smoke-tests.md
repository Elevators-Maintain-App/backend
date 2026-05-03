# API Smoke Tests

La suite de smoke tests valida contrato basico de endpoints core mobile sin depender de datos productivos, Firebase real ni Postgres real.

## Alcance inicial

Los tests en `tests/test_api/test_mobile_contract_smoke.py` cubren:

- Dashboards core mobile: technician, supervisorV2, admin y superadmin.
- Listados core de ordenes por admin/supervisor.
- Checklist load/get/update item.
- Seguimiento iniciar/reanudar/sync-validar/sync-finalizar/reporte-prerevision.

## Que validan

- La ruta existe.
- El metodo HTTP esperado no responde `404` ni `405`.
- El middleware de observabilidad sigue activo.
- La respuesta incluye `X-Request-ID`.

Todavia no validan payload completo ni datos reales. Los servicios, auth y DB se mockean dentro de la app de prueba para no cambiar guards reales ni tocar infraestructura.

## Como correr

Con Docker Compose:

```bash
docker compose run --rm api pytest tests/test_api/test_mobile_contract_smoke.py -q
```

Para correr tambien el smoke del middleware:

```bash
docker compose run --rm api pytest tests/test_api/test_observability_middleware.py tests/test_api/test_mobile_contract_smoke.py -q
```

## Restricciones

- No relajar auth en produccion.
- No cambiar rutas, response models ni payloads para hacer pasar estos tests.
- No usar datos productivos.
- Si un endpoint cambia de contrato, primero actualizar `docs/backend-mobile-contract.md` y coordinar compatibilidad mobile.
