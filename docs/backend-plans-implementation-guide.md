# VertiOne - Guia backend para implementar planes con Codex

## 1. Contexto del backend actual

El backend actual usa FastAPI, SQLAlchemy async, Alembic, Firebase Auth/Firestore y PostgreSQL.

Estructura relevante detectada:

```text
app/api/routes/
app/services/
app/db/models/
app/db/repositories/
app/schemas/
app/auth/firebase.py
app/main.py
migrations/versions/
tests/
```

Servicios activos importantes:

| Dominio | Ruta activa | Servicio activo |
| --- | --- | --- |
| Usuarios | `app/api/routes/usuarios.py` | `app/services/usuario/usuarios.py` |
| Clientes | `app/api/routes/clientes.py` | `app/services/cliente/cliente_servicio.py` |
| Proyectos | `app/api/routes/proyectos.py` | `app/services/proyectos/proyectos.py` |
| Unidades | `app/api/routes/unidades.py` | `app/services/unidades.py` |
| Ordenes | `app/api/routes/ordenes_de_trabajo.py` | `app/services/ordenes_de_trabajo.py` |
| Reportes PDF | `app/api/routes/ordenes_seguimiento.py` | `app/services/reportes/generar_pdf_service.py` |
| Checklists | `app/api/routes/checklists.py` | `app/services/checklists.py` |

Importante:

- No migrar rutas activas a servicios alternos durante esta funcionalidad.
- No cambiar contratos protegidos en `docs/backend-mobile-contract.md`.
- No introducir dependencias externas nuevas salvo que se justifique explicitamente.

## 2. Archivos nuevos esperados

Crear modelos:

```text
app/db/models/plans.py
```

Crear schemas:

```text
app/schemas/plans.py
app/schemas/subscriptions.py
```

Crear repositorios:

```text
app/db/repositories/plans.py
app/db/repositories/subscriptions.py
app/db/repositories/company_usage.py
```

Crear servicios:

```text
app/services/plans/__init__.py
app/services/plans/exceptions.py
app/services/plans/subscription_service.py
app/services/plans/usage_service.py
app/services/plans/plan_limits_service.py
```

Crear rutas:

```text
app/api/routes/plans.py
app/api/routes/subscriptions.py
```

Actualizar imports:

```text
app/db/models/__init__.py
migrations/env.py
app/main.py
```

Crear tests:

```text
tests/test_services/test_plans/
tests/test_api/test_plans_contract.py
tests/test_api/test_subscription_contract.py
```

## 3. Modelos exactos

### `Plan`

Tabla: `plans`

Usar `UUID(as_uuid=True)` como PK, igual que `Compania`, `Cliente`, `Proyecto`, `Unidad`.

Campos:

```text
id
code
name
description
max_admins
max_supervisors
max_technicians
max_clients
max_projects
max_units
max_work_orders_per_month
max_pdf_reports_per_month
storage_limit_mb
allow_offline_mode
allow_custom_checklists
allow_advanced_dashboard
allow_evidence_editing
is_public
is_active
created_at
updated_at
```

Relaciones:

```text
subscriptions = relationship("CompanySubscription", back_populates="plan")
```

### `CompanySubscription`

Tabla: `company_subscriptions`

Campos:

```text
id
company_id
plan_id
status
billing_period
start_date
end_date
trial_ends_at
last_payment_at
next_payment_due_at
cancelled_at
notes
created_at
updated_at
```

Relaciones:

```text
company = relationship("Compania", back_populates="subscriptions")
plan = relationship("Plan", back_populates="subscriptions")
```

### `CompanyUsage`

Tabla: `company_usage`

Campos:

```text
id
company_id
period_year
period_month
work_orders_created
pdf_reports_generated
storage_used_mb
created_at
updated_at
```

Constraint:

```text
UniqueConstraint("company_id", "period_year", "period_month", name="ux_company_usage_period")
```

Relaciones:

```text
company = relationship("Compania", back_populates="usage_periods")
```

### Actualizar `Compania`

Agregar relaciones:

```python
subscriptions = relationship("CompanySubscription", back_populates="company", cascade="all, delete-orphan")
usage_periods = relationship("CompanyUsage", back_populates="company", cascade="all, delete-orphan")
```

No agregar columna `plan_id` directamente a `companias` en la primera version. La suscripcion debe vivir en `company_subscriptions`.

## 4. Enums recomendados

Para reducir riesgo con Alembic/Postgres, en la primera version usar `String` validado por Pydantic/servicio, no `sqlalchemy.Enum`, salvo que el proyecto decida lo contrario explicitamente.

Valores aceptados:

```text
SubscriptionStatus = trial | active | past_due | suspended | cancelled | expired
BillingPeriod = monthly | yearly | pilot | custom
```

Estados que permiten acciones:

```text
trial
active
```

Estados que bloquean creaciones/acciones pagadas:

```text
past_due
suspended
cancelled
expired
```

## 5. Migracion Alembic

Crear una migracion en `migrations/versions/` posterior al head actual.

La migracion debe:

1. Crear tabla `plans`.
2. Crear tabla `company_subscriptions`.
3. Crear tabla `company_usage`.
4. Crear indices en `company_id`, `plan_id`, `code`.
5. Crear unique de `plans.code`.
6. Crear unique de `company_usage(company_id, period_year, period_month)`.
7. Insertar seed inicial de planes.

No crear datos de suscripcion para todas las companias automaticamente sin instruccion explicita. Si se necesita compatibilidad para companias existentes, hacerlo en un slice separado con decision comercial clara: asignar `free`, `pilot_partner` o `professional`.

## 6. Excepciones de plan

Crear `app/services/plans/exceptions.py`.

Clases recomendadas:

```python
class PlanLimitReachedException(HTTPException): ...
class PlanFeatureNotAllowedException(HTTPException): ...
class SubscriptionNotFoundException(HTTPException): ...
class SubscriptionNotActiveException(HTTPException): ...
```

Shape obligatorio para limite:

```json
{
  "detail": "Has alcanzado el limite de tecnicos de tu plan gratuito.",
  "code": "PLAN_LIMIT_REACHED",
  "resource": "technicians",
  "current_usage": 1,
  "plan_limit": 1
}
```

Shape obligatorio para feature:

```json
{
  "detail": "La edicion de evidencias no esta incluida en tu plan actual.",
  "code": "PLAN_FEATURE_NOT_ALLOWED",
  "feature": "evidence_editing"
}
```

Nota FastAPI:

- `HTTPException.detail` puede recibir dict. Usar dict para conservar `code`, `resource`, etc.
- El frontend debe leer `error.response.data.detail.code` si el backend devuelve dict dentro de `detail`.
- Si se decide devolver shape plano sin anidar, debe hacerse globalmente con exception handler; no hacerlo en el primer slice.

## 7. `UsageService`

Responsabilidades minimas:

```python
async def get_current_period_usage(company_id: UUID) -> CompanyUsage
async def count_users_by_role(company_id: UUID, role: Rol) -> int
async def count_clients(company_id: UUID) -> int
async def count_projects(company_id: UUID) -> int
async def count_units(company_id: UUID) -> int
async def count_work_orders_current_month(company_id: UUID) -> int
async def get_pdf_reports_generated_current_month(company_id: UUID) -> int
async def increment_work_orders_created(company_id: UUID) -> None
async def increment_pdf_reports_generated(company_id: UUID) -> None
async def get_company_usage_snapshot(company_id: UUID) -> dict
```

Regla de conteo:

- Usuarios: tabla `usuarios`, filtro `company_id`, `rol`, preferiblemente `is_active == True`.
- Clientes: tabla `clientes`, filtro `compania_id`.
- Proyectos: tabla `proyectos`, filtro `company_id`.
- Unidades: tabla `unidades`, filtro `company_id`.
- Ordenes mensuales: tabla `ordenes_de_trabajo`, filtro `company_id` y `created_at` en mes actual.
- PDF mensuales: `company_usage.pdf_reports_generated`.

## 8. `SubscriptionService`

Responsabilidades minimas:

```python
async def get_active_subscription(company_id: UUID) -> CompanySubscription
async def get_subscription_status(company_id: UUID) -> dict
async def assign_plan_to_company(company_id: UUID, payload: CompanySubscriptionAssign) -> CompanySubscription
async def update_company_subscription(company_id: UUID, payload: CompanySubscriptionUpdate) -> CompanySubscription
```

Criterio de suscripcion activa:

- `company_id` coincide.
- `status` en `trial`, `active`, `past_due`, `suspended` segun consulta administrativa.
- Para permitir uso, `status` debe ser `trial` o `active`.
- Si `end_date` existe y es anterior a la fecha actual, bloquear acciones como `expired` aunque el status no se haya actualizado.

## 9. `PlanLimitsService`

Responsabilidades minimas:

```python
async def assert_can_create_user(company_id: UUID, role: Rol) -> None
async def assert_can_create_client(company_id: UUID) -> None
async def assert_can_create_project(company_id: UUID) -> None
async def assert_can_create_unit(company_id: UUID) -> None
async def assert_can_create_work_order(company_id: UUID) -> None
async def assert_can_generate_pdf_report(company_id: UUID) -> None
async def assert_feature_enabled(company_id: UUID, feature_key: str) -> None
async def get_company_plan_status(company_id: UUID) -> CompanyPlanStatusOut
```

Logica comun:

```text
1. Obtener suscripcion de la compania.
2. Validar estado/vigencia.
3. Obtener plan.
4. Obtener limite del recurso o feature.
5. Obtener uso actual.
6. Si limite es null: permitir.
7. Si uso actual >= limite: bloquear.
8. Si uso actual < limite: permitir.
```

Para creaciones, usar `>=`, no `>`, porque el recurso todavia no se ha creado.

## 10. Puntos de integracion obligatorios

### 10.1 Usuarios

Archivo activo:

```text
app/services/usuario/usuarios.py
```

Metodo:

```text
UsuarioService.create(...)
```

Insertar validacion despues de normalizar `company_id` y antes de:

- subir foto a storage,
- crear usuario en Firebase,
- escribir Firestore,
- crear usuario en Postgres.

Regla:

```python
await PlanLimitsService(self.db).assert_can_create_user(company_id_normalizado, usuario_in.rol)
```

Cuidado:

- El metodo actualmente sube foto antes de normalizar y validar. El slice de planes debe mover la subida de foto despues de validar duplicados basicos y limite de plan, o al menos validar limite antes de subir.
- No romper recuperacion/rollback Firebase existente.

### 10.2 Clientes

Archivo activo:

```text
app/services/cliente/cliente_servicio.py
```

Metodo:

```text
create_cliente(...)
```

Validar despues de determinar/normalizar compania autorizada y antes de subir logo o guardar.

### 10.3 Proyectos

Archivo activo:

```text
app/services/proyectos/proyectos.py
```

Metodo:

```text
create(...)
```

Validar con `assert_can_create_project(company_id)` despues de resolver company_id segun rol.

### 10.4 Unidades

Archivo activo del router actual:

```text
app/services/unidades.py
```

Metodo:

```text
create(unidad_in, company_id)
```

Validar con `assert_can_create_unit(company_id)` antes de guardar.

No usar todavia `app/services/unidad/unidad_servicio.py` para esta ruta.

### 10.5 Ordenes de trabajo

Archivo activo:

```text
app/services/ordenes_de_trabajo.py
```

Metodo:

```text
create(...)
```

Validar con `assert_can_create_work_order(company_id)` antes de guardar.

Despues de creacion exitosa e idealmente despues de flush/commit exitoso de unidad de trabajo, incrementar uso mensual. Como el `get_db` hace commit al final del request, si se incrementa en la misma sesion y luego falla, el rollback debe revertir ambos cambios.

### 10.6 Reportes PDF

Archivo activo:

```text
app/services/reportes/generar_pdf_service.py
```

Funcion:

```text
generar_y_subir_pdf(orden_id, tipo)
```

Debe obtener la orden/checklist, determinar `company_id`, validar `assert_can_generate_pdf_report(company_id)`, generar PDF y despues incrementar `pdf_reports_generated` solo si se genero/subio correctamente.

Cuidado:

- Si el PDF ya existe y solo se retorna, no incrementar.
- Si falla WeasyPrint o storage, no incrementar.

### 10.7 Checklists personalizados

Archivo activo:

```text
app/services/checklists.py
```

Metodo:

```text
create_template_with_items(...)
```

Validar feature `custom_checklists` para la compania si el endpoint tiene contexto de compania. Si actualmente el template no tiene `company_id`, no redisenar todo en el primer slice; documentar limitacion y proteger solo cuando se agregue compania a templates.

## 11. Endpoints a crear

### `GET /api/subscription/me`

Roles:

```text
superAdmin, admin, supervisor, technician, client
```

Si `superAdmin` no tiene `company_id`, devolver 400 o permitir query administrativa por compania en endpoint separado. No inventar compania.

Respuesta: `CompanyPlanStatusOut`.

### `GET /api/plans`

Rol:

```text
superAdmin
```

Debe listar planes activos e inactivos para administracion.

### `POST /api/plans`

Rol:

```text
superAdmin
```

Debe crear plan validando `code` unico.

### `PATCH /api/plans/{plan_id}`

Rol:

```text
superAdmin
```

Debe actualizar campos comerciales y limites.

### `POST /api/subscription/companies/{company_id}`

Rol:

```text
superAdmin
```

Debe asignar plan a compania. Si existe suscripcion activa vigente, cerrarla/cancelarla segun regla definida en servicio y crear nueva suscripcion.

### `GET /api/subscription/companies/{company_id}`

Rol:

```text
superAdmin
```

Debe devolver el mismo snapshot de `/me`, pero para cualquier compania.

## 12. Tests obligatorios por slice

### Servicios

Crear tests unitarios para:

- Plan con limite `null` permite crear.
- Plan con uso menor que limite permite crear.
- Plan con uso igual al limite bloquea.
- Suscripcion `suspended` bloquea.
- Suscripcion vencida por `end_date` bloquea.
- Feature false bloquea.
- Feature true permite.

### API contract

Crear tests para:

- `GET /api/subscription/me` devuelve `plan`, `limits`, `usage`, `features`.
- Error de limite mantiene `code = PLAN_LIMIT_REACHED`.
- Error de feature mantiene `code = PLAN_FEATURE_NOT_ALLOWED`.

### Integracion sobre recursos

Minimo:

- Crear tecnico bloquea cuando `max_technicians` alcanzado.
- Crear proyecto bloquea cuando `max_projects` alcanzado.
- Crear unidad bloquea cuando `max_units` alcanzado.
- Crear orden bloquea cuando `max_work_orders_per_month` alcanzado.

No usar Firebase real en tests. Mockear Firebase/Auth/Firestore como ya se hace en tests de usuario.

## 13. Comandos de validacion

Codex debe ejecutar cuando aplique:

```bash
pytest tests/test_services/test_plans -q
pytest tests/test_api/test_subscription_contract.py -q
pytest tests/test_api -q
pytest tests -q
```

Si hay limitaciones de entorno por Firebase o DB, Codex debe reportarlas y dejar tests aislados/mocks.

## 14. Criterios de aceptacion globales

- Los modelos nuevos importan correctamente desde `app/db/models/__init__.py`.
- Alembic detecta/ejecuta migracion sin romper modelos existentes.
- `app/main.py` registra nuevos routers.
- No cambia ningun endpoint protegido de mobile.
- Los errores de plan son estructurados y consistentes.
- Las validaciones viven en servicios, no en componentes frontend ni solo en rutas.
- Los tests nuevos cubren happy path y bloqueos.
- No se incluye ningun secreto ni cambio de configuracion sensible.

