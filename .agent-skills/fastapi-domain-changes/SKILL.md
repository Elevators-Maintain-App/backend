---
name: fastapi-domain-changes
description: Usa esta skill cuando tengas que corregir o extender entidades de negocio en VertiOne Backend, especialmente usuarios, compañías, proyectos, unidades, órdenes o dashboards.
---

# FastAPI Domain Changes

## Objetivo
Hacer cambios de negocio sin romper la arquitectura en capas ni los contratos consumidos por la app móvil.

## Ruta mental
1. Identifica la entidad raíz.
2. Encuentra su ruta en `app/api/routes`.
3. Encuentra el service asociado.
4. Revisa repositorio, modelo y schemas.
5. Implementa el cambio de forma vertical completa.

## Orden recomendado de edición
1. `app/db/models/*`
2. `app/schemas/*`
3. `app/db/repositories/*`
4. `app/services/*`
5. `app/api/routes/*`

## Reglas
- No devuelvas ORM crudo si ya existe schema de salida.
- Valida permisos en servicio o dependencia de auth, no dispersos en cualquier lado.
- Usa errores 404, 403 y 400 cuando corresponda; evita 500 por casos esperables.
- Si el endpoint es multiempresa, filtra por `company_id` o por el rol correspondiente.

## Para dashboards y listados
- Evita N+1 cuando puedas; usa `selectinload` o consultas agregadas de forma consciente.
- Mantén nombres consistentes con el frontend.
- Si cambias enums o labels, confirma impacto en mobile.

## Qué evitar
- Agregar lógica de negocio nueva directamente en la ruta.
- Saltarse repositorios por “rapidez”.
- Cambiar el shape de respuesta sin actualizar schemas.

## Resultado esperado
Cambios trazables y mantenibles donde cada capa conserva su responsabilidad.
