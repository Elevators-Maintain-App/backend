# VertiOne - Arquitectura de planes, suscripciones y limites

## 1. Objetivo

Implementar un sistema de planes comerciales por compania que controle, desde backend, el acceso a recursos y funcionalidades de VertiOne sin romper el contrato actual de mobile ni web.

El sistema debe permitir:

- Asociar una compania a un plan activo.
- Definir limites por plan para usuarios, clientes, proyectos, unidades, ordenes y reportes.
- Definir features habilitadas o bloqueadas por plan.
- Registrar estado de suscripcion: trial, active, past_due, suspended, cancelled, expired.
- Registrar periodo de facturacion: monthly, yearly, pilot, custom.
- Validar limites antes de crear recursos o ejecutar acciones controladas.
- Entregar errores estructurados para que frontend muestre mensajes claros.
- Exponer un contrato de lectura para web/mobile con plan, uso, limites y features.

## 2. Principios de diseno

1. Backend es la fuente de verdad.
   El frontend puede ocultar botones, pero el backend siempre debe validar.

2. No romper endpoints existentes.
   Las rutas actuales documentadas en `docs/backend-mobile-contract.md` deben conservar su path, metodo, payload y respuesta salvo que se cree una version nueva.

3. Centralizar reglas de plan.
   No duplicar conteos, mensajes ni validaciones dentro de rutas. Usar servicios dedicados.

4. Validar antes de efectos secundarios.
   En creacion de usuarios, validar limite antes de crear usuario en Firebase/Auth/Firestore o subir imagenes. En PDF, validar antes de generar/subir archivo.

5. Errores predecibles.
   Todo bloqueo por plan debe usar el mismo shape de error.

6. Uso calculado primero; snapshots despues.
   Para el MVP, los conteos de entidades pueden calcularse con queries a tablas reales. `company_usage` debe usarse para contadores mensuales/eventos y cache operativo, no como unica fuente de verdad para cantidades vivas.

7. SuperAdmin puede administrar planes.
   Admin/supervisor/technician/client solo pueden consultar su estado de plan y recibir bloqueos.

## 3. Entidades nuevas

### 3.1 `plans`

Tabla catalogo de planes comerciales.

Campos obligatorios:

| Campo | Tipo sugerido | Notas |
| --- | --- | --- |
| id | UUID PK | `uuid.uuid4` |
| code | String unique | Ej: `free`, `pilot_partner`, `starter`, `professional`, `enterprise` |
| name | String | Nombre comercial |
| description | Text nullable | Descripcion visible/admin |
| max_admins | Integer nullable | `null` = ilimitado |
| max_supervisors | Integer nullable | `null` = ilimitado |
| max_technicians | Integer nullable | `null` = ilimitado |
| max_clients | Integer nullable | `null` = ilimitado |
| max_projects | Integer nullable | `null` = ilimitado |
| max_units | Integer nullable | `null` = ilimitado |
| max_work_orders_per_month | Integer nullable | `null` = ilimitado |
| max_pdf_reports_per_month | Integer nullable | `null` = ilimitado |
| storage_limit_mb | Integer nullable | Reservado para evidencias/storage |
| allow_offline_mode | Boolean | Default `false` salvo planes que lo incluyan |
| allow_custom_checklists | Boolean | Default `false` |
| allow_advanced_dashboard | Boolean | Default `false` |
| allow_evidence_editing | Boolean | Default `false` |
| is_public | Boolean | Si se puede mostrar comercialmente |
| is_active | Boolean | Si puede asignarse a nuevas companias |
| created_at | DateTime/TIMESTAMP | server default now |
| updated_at | DateTime/TIMESTAMP | server default/onupdate now |

Notas:

- Usar `code` para logica estable, no `name`.
- `null` en limites significa ilimitado. No usar `0` para ilimitado.
- `0` significa bloqueo total del recurso.

### 3.2 `company_subscriptions`

Tabla que relaciona companias con planes.

Campos obligatorios:

| Campo | Tipo sugerido | Notas |
| --- | --- | --- |
| id | UUID PK | `uuid.uuid4` |
| company_id | UUID FK `companias.id` | Indexado |
| plan_id | UUID FK `plans.id` | Indexado |
| status | String/Enum | `trial`, `active`, `past_due`, `suspended`, `cancelled`, `expired` |
| billing_period | String/Enum | `monthly`, `yearly`, `pilot`, `custom` |
| start_date | Date | Inicio comercial |
| end_date | Date nullable | Fin de vigencia, trial o piloto |
| trial_ends_at | Date nullable | Opcional |
| last_payment_at | DateTime nullable | Opcional |
| next_payment_due_at | Date nullable | Opcional |
| cancelled_at | DateTime nullable | Opcional |
| notes | Text nullable | Notas internas comerciales |
| created_at | DateTime/TIMESTAMP | server default now |
| updated_at | DateTime/TIMESTAMP | server default/onupdate now |

Reglas:

- Solo debe existir una suscripcion activa vigente por compania.
- Para evitar cambios riesgoso en migracion inicial, no crear constraint parcial compleja hasta validar motor/ambiente. Primero controlar desde servicio y tests.
- Estados que permiten uso: `trial`, `active`.
- Estados que deben bloquear acciones pagadas: `past_due`, `suspended`, `cancelled`, `expired`, salvo excepciones definidas por negocio.

### 3.3 `company_usage`

Tabla de uso mensual por compania.

Campos obligatorios:

| Campo | Tipo sugerido | Notas |
| --- | --- | --- |
| id | UUID PK | `uuid.uuid4` |
| company_id | UUID FK `companias.id` | Indexado |
| period_year | Integer | Ej: 2026 |
| period_month | Integer | 1-12 |
| work_orders_created | Integer | Contador mensual |
| pdf_reports_generated | Integer | Contador mensual |
| storage_used_mb | Integer | Reservado |
| created_at | DateTime/TIMESTAMP | server default now |
| updated_at | DateTime/TIMESTAMP | server default/onupdate now |

Constraints recomendados:

- Unique `(company_id, period_year, period_month)`.

No almacenar como fuente principal:

- `users_count`
- `projects_count`
- `clients_count`
- `units_count`

Esos conteos deben calcularse contra tablas reales para evitar desincronizacion. Si luego se necesita performance, se puede cachear con reconciliacion.

## 4. Recursos controlados

### 4.1 Usuarios por rol

Recurso tecnico/comercial:

| Rol DB | Resource key | Limite de plan |
| --- | --- | --- |
| `Rol.ADMIN` / `admin` | `admins` | `max_admins` |
| `Rol.SUPERVISOR` / `supervisor` | `supervisors` | `max_supervisors` |
| `Rol.TECHNICIAN` / `technician` | `technicians` | `max_technicians` |

No contar `superAdmin` contra la compania. SuperAdmin es rol de plataforma.

`client` debe contarse contra `max_clients` solo si se decide que cada usuario cliente representa un acceso de cliente. Para el MVP se recomienda controlar clientes corporativos con la tabla `clientes` y usuarios tipo client con una regla separada solo si el negocio lo pide.

### 4.2 Clientes

- Tabla: `clientes`
- FK: `compania_id`
- Resource key: `clients`
- Limite: `max_clients`

### 4.3 Proyectos

- Tabla: `proyectos`
- FK: `company_id`
- Resource key: `projects`
- Limite: `max_projects`

### 4.4 Unidades

- Tabla: `unidades`
- FK: `company_id`
- Resource key: `units`
- Limite: `max_units`

### 4.5 Ordenes de trabajo mensuales

- Tabla: `ordenes_de_trabajo`
- FK: `company_id`
- Fecha recomendada para periodo: `created_at`
- Resource key: `work_orders_per_month`
- Limite: `max_work_orders_per_month`

Para el MVP, se puede consultar conteo real por `created_at` entre inicio y fin del mes. En paralelo, incrementar `company_usage.work_orders_created` solo despues de creacion exitosa.

### 4.6 Reportes PDF mensuales

Generacion actual detectada:

- `app/api/routes/ordenes_seguimiento.py`
- `app/services/reportes/generar_pdf_service.py`
- Campos destino en `checklists`: `reporte_prerevision_url`, `reporte_final_url`

Resource key: `pdf_reports_per_month`

Limite: `max_pdf_reports_per_month`

Regla recomendada:

- Contar cada PDF nuevo generado y subido a storage.
- No incrementar si solo se consulta una URL existente.
- Validar antes de llamar a WeasyPrint/storage.

## 5. Features controladas

| Feature key | Campo de plan | Donde impacta |
| --- | --- | --- |
| `offline_mode` | `allow_offline_mode` | Mobile sync, colas offline, checklist sync |
| `custom_checklists` | `allow_custom_checklists` | Creacion/edicion de templates |
| `advanced_dashboard` | `allow_advanced_dashboard` | Dashboards avanzados web/mobile |
| `evidence_editing` | `allow_evidence_editing` | Reemplazo/edicion de evidencias por supervisor/admin |

Regla:

- Toda feature debe tener validacion en backend.
- Frontend puede ocultar UI segun `/api/subscription/me`, pero no decide autorizacion real.

## 6. Shape unico de errores de plan

Usar HTTP `403 Forbidden` para features bloqueadas y `409 Conflict` para limites alcanzados.

Limite alcanzado:

```json
{
  "detail": "Has alcanzado el limite de tecnicos de tu plan gratuito.",
  "code": "PLAN_LIMIT_REACHED",
  "resource": "technicians",
  "current_usage": 1,
  "plan_limit": 1
}
```

Feature bloqueada:

```json
{
  "detail": "La edicion de evidencias no esta incluida en tu plan actual.",
  "code": "PLAN_FEATURE_NOT_ALLOWED",
  "feature": "evidence_editing"
}
```

Suscripcion no valida:

```json
{
  "detail": "La suscripcion de la compania no esta activa.",
  "code": "SUBSCRIPTION_NOT_ACTIVE",
  "subscription_status": "suspended"
}
```

Sin suscripcion:

```json
{
  "detail": "La compania no tiene una suscripcion activa configurada.",
  "code": "SUBSCRIPTION_NOT_FOUND"
}
```

## 7. Servicios recomendados

Crear paquete:

```text
app/services/plans/
  __init__.py
  exceptions.py
  plan_limits_service.py
  subscription_service.py
  usage_service.py
```

Responsabilidades:

### `SubscriptionService`

- Obtener suscripcion activa/vigente de una compania.
- Validar estado de suscripcion.
- Asignar plan a compania desde superAdmin.
- Cambiar estado comercial.

### `UsageService`

- Obtener periodo actual.
- Crear o recuperar `company_usage` mensual.
- Contar recursos vivos: usuarios por rol, clientes, proyectos, unidades.
- Contar recursos mensuales: ordenes, reportes.
- Incrementar contadores mensuales solo despues de exito.

### `PlanLimitsService`

- `assert_can_create_user(company_id, rol)`
- `assert_can_create_client(company_id)`
- `assert_can_create_project(company_id)`
- `assert_can_create_unit(company_id)`
- `assert_can_create_work_order(company_id)`
- `assert_can_generate_pdf_report(company_id)`
- `assert_feature_enabled(company_id, feature_key)`
- `get_company_plan_status(company_id)`

## 8. Endpoints nuevos recomendados

Crear router:

```text
app/api/routes/plans.py
```

Registrar en `app/main.py`:

```python
app.include_router(plans_router, prefix="/api/plans", tags=["Plans"])
```

Crear router de suscripcion:

```text
app/api/routes/subscriptions.py
```

Registrar en `app/main.py`:

```python
app.include_router(subscriptions_router, prefix="/api/subscription", tags=["Subscription"])
```

### SuperAdmin

| Metodo | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/plans` | Listar planes |
| POST | `/api/plans` | Crear plan |
| PATCH | `/api/plans/{plan_id}` | Editar plan |
| GET | `/api/plans/{plan_id}` | Detalle de plan |
| POST | `/api/subscription/companies/{company_id}` | Asignar/cambiar plan |
| PATCH | `/api/subscription/companies/{company_id}` | Actualizar estado/periodo/fechas |
| GET | `/api/subscription/companies/{company_id}` | Ver suscripcion y uso de una compania |

### Compania autenticada

| Metodo | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/subscription/me` | Estado de plan, limites, uso y features de la compania del usuario actual |

## 9. Contrato de `/api/subscription/me`

Respuesta sugerida:

```json
{
  "company_id": "uuid",
  "subscription": {
    "id": "uuid",
    "status": "active",
    "billing_period": "monthly",
    "start_date": "2026-05-01",
    "end_date": null,
    "next_payment_due_at": "2026-06-01"
  },
  "plan": {
    "id": "uuid",
    "code": "pilot_partner",
    "name": "Piloto Partner",
    "description": "Plan piloto con limites ampliados"
  },
  "limits": {
    "admins": 2,
    "supervisors": 3,
    "technicians": 10,
    "clients": 5,
    "projects": 20,
    "units": 100,
    "work_orders_per_month": 300,
    "pdf_reports_per_month": 300,
    "storage_limit_mb": 1024
  },
  "usage": {
    "admins": 1,
    "supervisors": 1,
    "technicians": 4,
    "clients": 2,
    "projects": 8,
    "units": 25,
    "work_orders_per_month": 44,
    "pdf_reports_per_month": 38,
    "storage_used_mb": 120
  },
  "features": {
    "offline_mode": true,
    "custom_checklists": true,
    "advanced_dashboard": true,
    "evidence_editing": true
  },
  "warnings": []
}
```

## 10. Planes seed iniciales

Los valores exactos pueden ajustarse, pero Codex no debe inventarlos. Usar estos como base inicial si no hay instruccion posterior.

| code | name | admins | supervisors | technicians | clients | projects | units | work orders/mes | pdf/mes | offline | custom checklists | dashboard avanzado | evidencia |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| `free` | Gratuito | 1 | 1 | 1 | 1 | 1 | 5 | 20 | 20 | true | false | false | false |
| `pilot_partner` | Piloto Partner | 2 | 3 | 10 | 5 | 20 | 100 | 300 | 300 | true | true | true | true |
| `starter` | Starter | 1 | 2 | 5 | 3 | 10 | 50 | 150 | 150 | true | false | false | false |
| `professional` | Professional | 3 | 5 | 20 | 10 | 50 | 300 | 1000 | 1000 | true | true | true | true |
| `enterprise` | Enterprise | null | null | null | null | null | null | null | null | true | true | true | true |

## 11. Integraciones iniciales obligatorias

Primera fase de enforcement:

- `UsuarioService.create`
- `ClienteService.create_cliente`
- `ProyectoService.create`
- `UnidadService.create` activo en `app/services/unidades.py`
- `OrdenDeTrabajoService.create` activo en `app/services/ordenes_de_trabajo.py`
- `generar_y_subir_pdf` en `app/services/reportes/generar_pdf_service.py`
- `ChecklistService.create_template_with_items` para `allow_custom_checklists`

No migrar servicios legacy a nuevos paquetes durante esta implementacion. Integrar sobre los servicios actualmente activos.

## 12. No objetivos de la primera version

No implementar todavia:

- Pasarela de pago real.
- Facturacion electronica.
- Upgrade self-service desde frontend.
- Reconciliacion avanzada de storage.
- Multi-currency.
- Webhooks de pago.
- Refactor completo de rutas legacy.

