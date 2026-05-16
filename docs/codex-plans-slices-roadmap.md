# VertiOne - Roadmap de slices para Codex: planes y suscripciones

## 1. Regla general para Codex

Trabajar en slices pequenos, verificables y sin decisiones de producto improvisadas.

Antes de modificar codigo, Codex debe leer:

```text
docs/plans-subscriptions-architecture.md
docs/backend-plans-implementation-guide.md
docs/plans-api-frontend-contract.md
docs/backend-mobile-contract.md
docs/web-development-rules.md
```

Codex no debe:

- Cambiar rutas existentes sin instruccion explicita.
- Refactorizar servicios legacy fuera del alcance del slice.
- Cambiar payloads de mobile.
- Agregar pasarela de pagos.
- Usar Firebase real en tests.
- Introducir secretos.
- Inventar limites comerciales distintos a los definidos en docs.

## 2. Slice 1 - Base de datos y modelos

### Objetivo

Agregar modelos, migracion y seed inicial de planes sin enforcement todavia.

### Alcance

Crear:

```text
app/db/models/plans.py
app/db/repositories/plans.py
app/db/repositories/subscriptions.py
app/db/repositories/company_usage.py
app/schemas/plans.py
app/schemas/subscriptions.py
migrations/versions/<revision>_add_plans_subscriptions_usage.py
```

Actualizar:

```text
app/db/models/__init__.py
app/db/models/compania.py
migrations/env.py
```

### Criterios de aceptacion

- Existen tablas `plans`, `company_subscriptions`, `company_usage`.
- `plans.code` es unico.
- `company_usage(company_id, period_year, period_month)` es unico.
- Seed inicial crea planes: `free`, `pilot_partner`, `starter`, `professional`, `enterprise`.
- No hay validaciones aplicadas todavia a creacion de recursos.
- Tests de import/modelos pasan.

### Tests sugeridos

```bash
pytest tests/test_services/test_plans -q
pytest tests -q
```

## 3. Slice 2 - Servicios de suscripcion, uso y limites

### Objetivo

Crear servicios puros de negocio para consultar suscripcion, calcular uso y validar limites/features.

### Alcance

Crear:

```text
app/services/plans/__init__.py
app/services/plans/exceptions.py
app/services/plans/subscription_service.py
app/services/plans/usage_service.py
app/services/plans/plan_limits_service.py
```

### Criterios de aceptacion

- `PlanLimitsService` expone metodos `assert_can_*` definidos en guia.
- Limite `null` se interpreta como ilimitado.
- Uso `>= limite` bloquea.
- Suscripcion vencida o suspendida bloquea.
- Errores tienen codes oficiales.
- Tests unitarios cubren happy path y bloqueos.

### Tests sugeridos

```bash
pytest tests/test_services/test_plans -q
```

## 4. Slice 3 - Endpoints de lectura y administracion

### Objetivo

Exponer endpoints para que web/mobile puedan consultar estado de plan y SuperAdmin pueda administrar planes/suscripciones.

### Alcance

Crear:

```text
app/api/routes/plans.py
app/api/routes/subscriptions.py
```

Actualizar:

```text
app/main.py
```

Endpoints minimos:

```text
GET /api/subscription/me
GET /api/subscription/companies/{company_id}
POST /api/subscription/companies/{company_id}
PATCH /api/subscription/companies/{company_id}
GET /api/plans
POST /api/plans
PATCH /api/plans/{plan_id}
GET /api/plans/{plan_id}
```

### Criterios de aceptacion

- Rutas nuevas registradas.
- `GET /api/subscription/me` devuelve `subscription`, `plan`, `limits`, `usage`, `features`, `warnings`.
- Endpoints admin requieren `superAdmin`.
- No se cambia ningun endpoint existente.
- Tests de contrato API pasan con mocks.

### Tests sugeridos

```bash
pytest tests/test_api/test_subscription_contract.py -q
pytest tests/test_api/test_plans_contract.py -q
```

## 5. Slice 4 - Enforcement en usuarios, clientes, proyectos y unidades

### Objetivo

Aplicar limites a recursos maestros.

### Alcance

Modificar:

```text
app/services/usuario/usuarios.py
app/services/cliente/cliente_servicio.py
app/services/proyectos/proyectos.py
app/services/unidades.py
```

### Criterios de aceptacion

- Crear tecnico/admin/supervisor valida limite por rol antes de Firebase/storage.
- Crear cliente valida `max_clients`.
- Crear proyecto valida `max_projects`.
- Crear unidad valida `max_units`.
- Errores usan `PLAN_LIMIT_REACHED`.
- Tests cubren al menos tecnico/proyecto/unidad bloqueados.

### Tests sugeridos

```bash
pytest tests/test_services/test_usuario -q
pytest tests/test_api/test_usuario_client_creation_rules.py -q
pytest tests/test_api -q
```

## 6. Slice 5 - Enforcement en ordenes y reportes PDF

### Objetivo

Controlar consumo mensual de ordenes de trabajo y reportes PDF.

### Alcance

Modificar:

```text
app/services/ordenes_de_trabajo.py
app/services/reportes/generar_pdf_service.py
```

### Criterios de aceptacion

- Crear orden valida `max_work_orders_per_month`.
- Crear orden exitosa incrementa uso mensual o queda reflejada en conteo real.
- Generar PDF valida `max_pdf_reports_per_month` antes de WeasyPrint/storage.
- PDF exitoso incrementa `pdf_reports_generated`.
- Fallo de PDF no incrementa uso.
- Consultar PDF existente no incrementa uso.

### Tests sugeridos

```bash
pytest tests/test_services/test_ordenes_de_trabajo_service.py -q
pytest tests/test_api/test_mobile_contract_smoke.py -q
pytest tests/test_api -q
```

## 7. Slice 6 - Feature flags por plan

### Objetivo

Aplicar features booleanas de plan en puntos funcionales.

### Alcance inicial

- `allow_custom_checklists`: proteger creacion de templates si hay contexto de compania.
- `allow_evidence_editing`: proteger endpoints/servicios de edicion de evidencia cuando esten identificados.
- `allow_advanced_dashboard`: devolver flag para frontend; no bloquear dashboards existentes hasta definir cuales son premium.
- `allow_offline_mode`: devolver flag para mobile; no romper sync offline existente sin diseno especifico.

### Criterios de aceptacion

- Feature false produce `PLAN_FEATURE_NOT_ALLOWED`.
- Feature true permite accion.
- No se bloquean funcionalidades criticas legacy sin definir impacto.

## 8. Slice 7 - Documentacion final backend

### Objetivo

Actualizar docs con decisiones implementadas y comandos reales.

### Alcance

Actualizar:

```text
docs/plans-subscriptions-architecture.md
docs/backend-plans-implementation-guide.md
docs/plans-api-frontend-contract.md
docs/backend-mobile-contract.md si aplica, sin modificar contrato legacy
```

### Criterios de aceptacion

- Docs reflejan endpoints reales.
- Docs reflejan limites seed reales.
- Docs incluyen errores reales.
- Docs incluyen comandos de test ejecutados.

## 9. Slices frontend posteriores

No implementar frontend hasta terminar al menos slices 1-3 de backend.

### Web slice futuro

Crear:

```text
src/types/subscription.ts
src/services/subscription.service.ts
src/hooks/use-subscription.ts
src/lib/plan-errors.ts
```

Integrar en dashboard/sidebar/mensajes.

### Mobile slice futuro

Crear:

```text
src/services/subscription/subscription.types.ts
src/services/subscription/index.ts
src/hooks/queries/use-subscription-query.ts
src/utils/plan-errors.ts
```

Integrar con mutations y sync offline.

## 10. Definition of Done global

Un slice se considera terminado solo si:

- El codigo compila/importa.
- Hay tests nuevos o actualizados.
- Se ejecutaron comandos de prueba relevantes.
- No se alteraron contratos protegidos.
- Los errores estan estructurados.
- No quedaron TODOs criticos sin documentar.
- Codex reporta archivos modificados y razon de cada cambio.

