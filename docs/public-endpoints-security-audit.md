# Public Endpoints Security Audit

Auditoria estatica de endpoints FastAPI que no declaran `get_current_firebase_user`, `require_role` ni una dependencia equivalente de autenticacion/autorizacion en la ruta. No se cambia comportamiento en esta fase.

## Alcance

- Fecha de auditoria: 2026-05-03.
- Base revisada: routers registrados en `app/main.py` y `app/api/routes/*`.
- Criterio: se marca como publico si la ruta solo usa `get_db` u otras dependencias no relacionadas con auth.
- Limitacion: esta auditoria es estatica. Antes de cerrar rutas se debe medir uso real con observabilidad por `path`, `method`, `status_code`, `x-app-platform` y `x-app-version`.

## Resumen ejecutivo

- Riesgo critico: mutaciones publicas restantes de base operativa, dashboards admin legacy publicos y rutas publicas de lectura de usuario.
- Riesgo alto: relaciones publicas por cliente, hojas de vida CRUD publico, zonas geograficas CRUD publico, PDF de checklist publico.
- Riesgo medio: catalogos publicos de solo lectura y LOV no multiempresa.
- Riesgo bajo: health check.

## Matriz de endpoints publicos

| Metodo | Ruta | Router/archivo | Auth actual | Tipo | Datos expuestos | Riesgo | Posible consumidor | Accion recomendada |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GET | `/` | `app/main.py` | Publico | health | Estado basico de API. | Bajo | infra / healthcheck | Mantener publico; limitar contenido a health basico. |
| GET | `/api/dashboard/usuarios` | `admin_dashboard.py` | Publico, solo `get_db` | read | Listas de tecnicos, supervisores y clientes. Puede incluir datos personales segun modelo. | Critico | legacy / unknown | Proteger primero con `superAdmin` o reemplazo protegido; medir uso antes de cerrar. |
| GET | `/api/dashboard/estadisticas/usuarios` | `admin_dashboard.py` | Publico, solo `get_db` | read | Conteos de tecnicos, supervisores y clientes. | Alto | legacy / unknown | Proteger con `superAdmin` o mover a dashboard protegido. |
| GET | `/api/dashboard/ordenes-trabajo/resumen` | `dashboard.py` legacy | Publico, solo `get_db` | read | Conteos globales de ordenes por estado, sin filtro de compania. | Alto | legacy / unknown | Crear alternativa protegida multiempresa; medir uso antes de cerrar. |
| GET | `/api/dashboard/unidades/mantenimiento-pendiente` | `dashboard.py` legacy | Publico, solo `get_db` | read | Unidades sin hoja de vida, potencial inventario operativo. | Alto | legacy / unknown | Proteger con rol operativo/admin; validar consumidor antes. |
| GET | `/api/dashboard/estadisticas/general` | `dashboard.py` legacy | Publico, solo `get_db` | read | Estadisticas globales de ordenes por prioridad, estado y tipo. | Alto | legacy / unknown | Proteger o reemplazar con endpoint por compania. |
| GET | `/api/clientes/{cliente_id}/proyectos` | `clientes.py` | Publico, solo `get_db` | read | Proyectos asociados a un cliente. | Alto | legacy / web futura / unknown | Agregar alternativa protegida con filtro por compania/cliente; medir uso. |
| GET | `/api/clientes/{cliente_id}/unidades` | `clientes.py` | Publico, solo `get_db` | read | Unidades asociadas a un cliente. | Alto | legacy / web futura / unknown | Proteger con rol permitido y filtro multiempresa. |
| GET | `/api/clientes/{cliente_id}/ordenes-trabajo` | `clientes.py` | Publico, solo `get_db` | read | Ordenes de trabajo asociadas a un cliente. | Critico | legacy / unknown | Proteger antes que relaciones menos sensibles; requiere prueba de mobile/admin. |
| GET | `/api/checklists/{orden_id}/reporte.pdf` | `checklists.py` | Publico, solo `get_db` | report | PDF de checklist con items, observaciones y posibles evidencias/datos operativos. | Critico | legacy / mobile / unknown | Medir uso; crear URL protegida o firmada; no cerrar sin confirmar consumidor. |
| GET | `/api/usuarios/{uid}` | `usuarios.py` | Publico, solo `get_db` | read | Datos de usuario por UID desde servicio de usuarios. | Critico | legacy / unknown | Proteger con self/admin/supervisor segun contrato; revisar rutas shadowed antes de tocar. |
| GET | `/api/lov/niveles-tecnicos` | `lov.py` | Publico, solo `get_db` | catalog | IDs/nombres de niveles tecnicos. | Medio | mobile / web futura | Puede mantenerse temporalmente; decidir si catalogos LOV read-only requieren token. |
| GET | `/api/lov/paises` | `lov.py` | Publico, solo `get_db` | catalog | IDs/nombres de paises. | Bajo | mobile / web futura | Candidato a mantenerse publico o cacheado. |
| GET | `/api/lov/tipos-documento` | `lov.py` | Publico, solo `get_db` | catalog | IDs/nombres de tipos de documento. | Medio | mobile / web futura | Mantener temporalmente; proteger si se estandariza auth para LOV. |
| GET | `/api/lov/tipos-unidad` | `lov.py` | Publico, solo `get_db` | catalog | IDs/nombres de tipos de unidad. | Medio | mobile / web futura | Mantener temporalmente; medir uso mobile. |
| GET | `/api/lov/prioridades` | `lov.py` | Publico, solo `get_db` | catalog | IDs/nombres de prioridades. | Medio | mobile / web futura | Mantener temporalmente; medir uso mobile. |
| GET | `/api/lov/tipos-orden` | `lov.py` | Publico, solo `get_db` | catalog | Tipos de orden paginados y total. | Medio | mobile / web futura | Mantener temporalmente; medir uso mobile. |
| GET | `/api/niveles-tecnicos/` | `nivel_tecnico.py` | Publico, solo `get_db` | catalog | Lista de niveles tecnicos. | Medio | mobile / web futura / legacy | Unificar politica con `/api/lov/niveles-tecnicos`. |
| GET | `/api/estados-orden/` | `estados_orden.py` | Publico, solo `get_db` | catalog | Estados de orden. | Medio | mobile / web futura / legacy | Mantener temporalmente; proteger o migrar a LOV protegido si procede. |
| GET | `/api/estados-orden/{estado_orden_id}` | `estados_orden.py` | Publico, solo `get_db` | catalog | Estado de orden por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/prioridades/` | `prioridades.py` | Publico, solo `get_db` | catalog | Prioridades. | Medio | mobile / web futura / legacy | Mantener temporalmente; medir uso. |
| GET | `/api/prioridades/{prioridad_id}` | `prioridades.py` | Publico, solo `get_db` | catalog | Prioridad por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/tipos-documento/` | `tipos_documento.py` | Publico, solo `get_db` | catalog | Tipos de documento. | Medio | mobile / web futura / legacy | Mantener temporalmente; medir uso. |
| GET | `/api/tipos-documento/{tipo_documento_id}` | `tipos_documento.py` | Publico, solo `get_db` | catalog | Tipo de documento por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/tipos-evidencia/` | `tipos_evidencia.py` | Publico, solo `get_db` | catalog | Tipos de evidencia. | Medio | mobile / web futura / legacy | Mantener temporalmente; medir uso. |
| GET | `/api/tipos-evidencia/{tipo_evidencia_id}` | `tipos_evidencia.py` | Publico, solo `get_db` | catalog | Tipo de evidencia por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/tipos-orden/` | `tipos_orden.py` | Publico, solo `get_db` | catalog | Tipos de orden. | Medio | mobile / web futura / legacy | Mantener temporalmente; medir uso. |
| GET | `/api/tipos-orden/{tipo_orden_id}` | `tipos_orden.py` | Publico, solo `get_db` | catalog | Tipo de orden por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/tipos-unidad/` | `tipos_unidad.py` | Publico, solo `get_db` | catalog | Tipos de unidad. | Medio | mobile / web futura / legacy | Mantener temporalmente; medir uso. |
| GET | `/api/tipos-unidad/{tipo_unidad_id}` | `tipos_unidad.py` | Publico, solo `get_db` | catalog | Tipo de unidad por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo. |
| GET | `/api/hojas-vida/` | `hojas_de_vida.py` | Publico, solo `get_db` | read | Lista de hojas de vida de unidades. | Alto | legacy / unknown | Proteger con rol operativo/admin; revisar contrato antes. |
| GET | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | Publico, solo `get_db` | read | Hoja de vida por ID. | Alto | legacy / unknown | Proteger con filtro por compania/unidad. |
| POST | `/api/hojas-vida/` | `hojas_de_vida.py` | Publico, solo `get_db` | mutation | Crea hoja de vida. | Critico | legacy / unknown | Proteger primero; posible `admin`/`supervisor`. |
| PUT | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | Publico, solo `get_db` | mutation | Actualiza hoja de vida. | Critico | legacy / unknown | Proteger primero; validar permisos por compania. |
| DELETE | `/api/hojas-vida/{hoja_id}` | `hojas_de_vida.py` | Publico, solo `get_db` | mutation | Elimina hoja de vida. | Critico | legacy / unknown | Proteger primero; alto riesgo de perdida de datos. |
| GET | `/api/zonas-geograficas/` | `zonas_geograficas.py` | Publico, solo `get_db` | catalog | Zonas geograficas. | Medio | mobile / web futura / legacy | Puede mantenerse temporalmente; medir uso. |
| GET | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | Publico, solo `get_db` | catalog | Zona geografica por ID. | Medio | legacy / unknown | Medir uso; proteger junto al catalogo si procede. |
| POST | `/api/zonas-geograficas/` | `zonas_geograficas.py` | Publico, solo `get_db` | mutation | Crea zona geografica. | Critico | legacy / unknown | Proteger primero; probable `superAdmin`/admin. |
| PUT | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | Publico, solo `get_db` | mutation | Actualiza zona geografica. | Critico | legacy / unknown | Proteger primero. |
| DELETE | `/api/zonas-geograficas/{zona_id}` | `zonas_geograficas.py` | Publico, solo `get_db` | mutation | Elimina zona geografica. | Critico | legacy / unknown | Proteger primero. |

## Rutas revisadas que si declaran auth

- `/api/lov/roles`: usa `get_current_firebase_user`.
- `/api/lov/companias`: usa `require_role("superAdmin")`.
- `/api/lov/clientes`, `/api/lov/proyectos`, `/api/lov/unidades`, `/api/lov/tecnicos`, `/api/lov/supervisores`: usan `require_role("superAdmin", "admin", "supervisor")`.
- Dashboards mobile principales: `/api/dashboard/technician`, `/api/dashboard/supervisorV2`, `/api/dashboard/admin`, `/api/dashboard/superadmin`, `/api/dashboard/cliente` declaran auth/roles.
- Checklists/sync/seguimiento mobile principales declaran `require_role`.
- Ordenes de trabajo core mobile/admin/supervisor/technician declaran `require_role` o `get_current_firebase_user`.

## Observaciones especiales

- `app/api/routes/usuarios.py` registra `GET /{uid}` publico antes de rutas estaticas como `/count` y `/all`. Por orden de FastAPI, algunas rutas de un solo segmento pueden quedar shadowed por el handler publico. No reordenar sin pruebas de contrato.
- `GET /api/usuarios/{uid}` se declara dos veces: una version publica al inicio y otra protegida al final. La primera probablemente gana por orden de registro.
- `PUT /api/usuarios/{uid}` fue mitigado el 2026-05-03: ahora requiere `require_role("superAdmin", "admin")`. No se reordenaron rutas ni se cambio payload/response model.
- Mutaciones `POST` de catalogos base mitigadas el 2026-05-03: `/api/estados-orden/`, `/api/prioridades/`, `/api/tipos-documento/`, `/api/tipos-evidencia/`, `/api/tipos-orden/` y `/api/tipos-unidad/` ahora requieren `require_role("superAdmin", "admin")`. Los `GET` de esos catalogos siguen publicos temporalmente.
- Algunos catalogos y datos base aun tienen lecturas publicas. Las mutaciones de catalogos base listadas arriba ya fueron protegidas; quedan pendientes mutaciones publicas de `hojas-vida` y `zonas-geograficas`.
- Las rutas publicas legacy de dashboard no aplican filtro multiempresa visible en la ruta.
- El PDF inline de checklist no valida rol ni pertenencia de la orden en la ruta; puede exponer datos operativos por UUID si el identificador se filtra.

## Fase posterior propuesta

### Proteger primero

- Mutaciones publicas restantes: CRUD de `hojas-vida` y CRUD mutante de `zonas-geograficas`.
- Dashboards admin legacy publicos: `/api/dashboard/usuarios`, `/api/dashboard/estadisticas/usuarios`.

### Necesitan alternativa protegida

- `GET /api/checklists/{orden_id}/reporte.pdf`: crear alternativa con auth o URL firmada/temporal.
- Relaciones de cliente: `/api/clientes/{cliente_id}/proyectos`, `/unidades`, `/ordenes-trabajo`.
- Dashboards legacy globales: `/api/dashboard/ordenes-trabajo/resumen`, `/api/dashboard/unidades/mantenimiento-pendiente`, `/api/dashboard/estadisticas/general`.

### Mantener temporalmente

- Health check `/`.
- LOV/catalogos read-only usados por mobile onboarding o formularios: `paises`, `tipos-documento`, `tipos-unidad`, `prioridades`, `tipos-orden`, `niveles-tecnicos`.
- Lecturas de zonas geograficas si mobile las usa para formularios.

### Medir antes de tocar

- Todos los endpoints publicos con `possible consumer = legacy / unknown`.
- Catalogos duplicados entre `/api/lov/*` y routers `tipos-*`.
- Rutas de usuarios shadowed para confirmar que clientes reales no dependen del comportamiento actual.

## Recomendaciones de implementacion segura

- No cerrar rutas en bloque.
- Agregar smoke tests de status esperado antes de aplicar auth.
- Usar observabilidad por `method`, `path`, `status_code`, `x-app-platform` y `x-app-version` para identificar consumidores.
- Para cada cierre, preferir primero alternativa protegida + periodo de medicion.
- Mantener response models y payloads durante la transicion.
