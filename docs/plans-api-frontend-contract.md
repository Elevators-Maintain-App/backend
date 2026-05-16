# VertiOne - Contrato API de planes para web y mobile

## 1. Objetivo

Definir el contrato que el backend debe exponer para que frontend web y React Native puedan mostrar el estado del plan, bloquear acciones de forma amigable y manejar errores de limites sin depender de logica comercial duplicada.

Este documento no implementa UI. Solo define respuestas, codigos y expectativas para consumidores.

## 2. Principios para frontend

1. Backend siempre decide.
   El frontend puede ocultar acciones, pero debe asumir que el backend puede rechazar cualquier operacion por plan.

2. Manejar errores por `code`.
   No depender del texto exacto de `detail` porque puede cambiar por tono comercial.

3. Mostrar mensajes accionables.
   Si llega `PLAN_LIMIT_REACHED`, mostrar recurso, uso actual y limite.

4. No romper offline.
   Mobile debe considerar que un bloqueo por plan puede ocurrir al sincronizar una accion que se hizo offline. En ese caso no debe borrar la cola local hasta resolver el conflicto.

## 3. Endpoint principal

### `GET /api/subscription/me`

Autenticacion:

```text
Bearer Firebase token
```

Roles permitidos:

```text
admin
supervisor
technician
client
superAdmin con company_id valido
```

Respuesta exitosa:

```json
{
  "company_id": "28dbcc72-7d6b-46c3-a201-4cb762ccfc92",
  "subscription": {
    "id": "bdfefefa-9456-4a82-8c8c-40bd78876921",
    "status": "active",
    "billing_period": "monthly",
    "start_date": "2026-05-01",
    "end_date": null,
    "trial_ends_at": null,
    "next_payment_due_at": "2026-06-01"
  },
  "plan": {
    "id": "8f2cc037-9e34-4484-8339-1c09da3ee27a",
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

## 4. Semantica de limites

- `null` significa ilimitado.
- `0` significa que el recurso no esta permitido.
- Si `usage[resource] >= limits[resource]`, frontend debe tratar el recurso como bloqueado.
- Si el limite es `null`, no mostrar barra de progreso porcentual salvo que UI tenga una etiqueta "Ilimitado".

## 5. Resource keys oficiales

Usar exactamente estos keys:

```text
admins
supervisors
technicians
clients
projects
units
work_orders_per_month
pdf_reports_per_month
storage_limit_mb
```

## 6. Feature keys oficiales

Usar exactamente estos keys:

```text
offline_mode
custom_checklists
advanced_dashboard
evidence_editing
```

## 7. Codigos de error oficiales

### 7.1 Limite alcanzado

HTTP recomendado: `409 Conflict`.

```json
{
  "detail": {
    "message": "Has alcanzado el limite de tecnicos de tu plan gratuito.",
    "code": "PLAN_LIMIT_REACHED",
    "resource": "technicians",
    "current_usage": 1,
    "plan_limit": 1
  }
}
```

Frontend debe soportar tambien esta variante si se decide shape plano mas adelante:

```json
{
  "message": "Has alcanzado el limite de tecnicos de tu plan gratuito.",
  "code": "PLAN_LIMIT_REACHED",
  "resource": "technicians",
  "current_usage": 1,
  "plan_limit": 1
}
```

### 7.2 Feature no permitida

HTTP recomendado: `403 Forbidden`.

```json
{
  "detail": {
    "message": "La edicion de evidencias no esta incluida en tu plan actual.",
    "code": "PLAN_FEATURE_NOT_ALLOWED",
    "feature": "evidence_editing"
  }
}
```

### 7.3 Suscripcion no activa

HTTP recomendado: `403 Forbidden`.

```json
{
  "detail": {
    "message": "La suscripcion de la compania no esta activa.",
    "code": "SUBSCRIPTION_NOT_ACTIVE",
    "subscription_status": "suspended"
  }
}
```

### 7.4 Suscripcion inexistente

HTTP recomendado: `403 Forbidden` o `404 Not Found` segun endpoint.

```json
{
  "detail": {
    "message": "La compania no tiene una suscripcion activa configurada.",
    "code": "SUBSCRIPTION_NOT_FOUND"
  }
}
```

## 8. Recomendacion para web frontend

Estructura detectada:

```text
src/lib/api-client.ts
src/services/
src/hooks/
src/types/
src/components/feedback/
src/components/layout/
```

Archivos sugeridos para implementar consumo:

```text
src/types/subscription.ts
src/services/subscription.service.ts
src/hooks/use-subscription.ts
src/lib/plan-errors.ts
```

Responsabilidades:

- `subscription.service.ts`: llamar `/api/subscription/me`.
- `use-subscription.ts`: cachear estado de plan para dashboard.
- `plan-errors.ts`: normalizar errores de backend a un shape consistente.
- Componentes existentes `ErrorState`, `StatusBadge`, `AppCard` pueden usarse para mensajes visuales.

Bloqueos visuales recomendados:

- Deshabilitar boton de crear cuando recurso esta al limite.
- Mostrar badge de plan en navbar/sidebar.
- Mostrar alerta si `subscription.status` no es `active` o `trial`.
- Mostrar uso tipo `4 / 10 tecnicos`.

## 9. Recomendacion para React Native

Estructura detectada:

```text
src/services/
src/hooks/queries/
src/hooks/mutations/
src/context/AuthContext.tsx
src/constants/query-keys.ts
src/services/sync/
```

Archivos sugeridos:

```text
src/services/subscription/subscription.types.ts
src/services/subscription/index.ts
src/hooks/queries/use-subscription-query.ts
src/utils/plan-errors.ts
```

Responsabilidades:

- Consultar `/api/subscription/me` despues de login y al entrar a dashboard.
- Usar React Query con query key estable, por ejemplo `['subscription', 'me']`.
- En mutations de usuarios/clientes/proyectos/unidades/ordenes, capturar `PLAN_LIMIT_REACHED`.
- En sync offline, si llega error de plan, marcar item como bloqueado/conflicto y no eliminar evidencia local automaticamente.

## 10. Mensajes UI sugeridos

### Limite de usuarios

```text
Has alcanzado el limite de tecnicos de tu plan actual. Uso actual: 1 de 1.
```

CTA opcional:

```text
Contactar soporte para ampliar el plan
```

### Feature bloqueada

```text
Esta funcion no esta incluida en tu plan actual.
```

### Suscripcion suspendida

```text
La suscripcion de esta compania no esta activa. Algunas acciones pueden estar bloqueadas.
```

## 11. Acciones que frontend debe considerar controladas

| Accion | Backend valida | Frontend puede ocultar/deshabilitar |
| --- | --- | --- |
| Crear usuario admin/supervisor/technician | Si | Si |
| Crear cliente | Si | Si |
| Crear proyecto | Si | Si |
| Crear unidad | Si | Si |
| Crear orden de trabajo | Si | Si |
| Generar PDF | Si | Si |
| Editar evidencia | Si | Si |
| Usar checklists personalizados | Si | Si |
| Usar modo offline/sync | Si | Parcial, con cuidado |

## 12. Comportamiento offline recomendado

Mobile no debe asumir que un dato creado offline sigue permitido al sincronizar.

Si al sincronizar una orden/checklist/reporte el backend responde:

```text
PLAN_LIMIT_REACHED
SUBSCRIPTION_NOT_ACTIVE
PLAN_FEATURE_NOT_ALLOWED
```

Entonces:

1. Mantener datos locales.
2. Marcar registro como `blocked_by_plan` o estado equivalente.
3. Mostrar mensaje al usuario.
4. Permitir reintentar despues de resolver plan.
5. No limpiar fotos, firmas ni payload local.

## 13. Criterios de aceptacion frontend futuros

- Web y mobile leen `/api/subscription/me`.
- Errores de plan se reconocen por `code`, no por texto.
- Botones principales se deshabilitan cuando el plan esta al limite.
- Mobile no borra cola offline ante error de plan.
- El usuario recibe mensajes claros y accionables.

