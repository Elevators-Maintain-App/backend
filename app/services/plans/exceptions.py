class PlanServiceError(Exception):
    code = "PLAN_SERVICE_ERROR"

    def __init__(self, message: str | None = None):
        self.message = message or "Error en el servicio de planes."
        super().__init__(self.message)


class InvalidPlanResourceError(PlanServiceError):
    code = "INVALID_PLAN_RESOURCE"

    def __init__(self, resource: str):
        self.resource = resource
        super().__init__(f"Recurso de plan no soportado: {resource}")


class InvalidPlanFeatureError(PlanServiceError):
    code = "INVALID_PLAN_FEATURE"

    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(f"Feature de plan no soportada: {feature}")


class SubscriptionNotFoundError(PlanServiceError):
    code = "SUBSCRIPTION_NOT_FOUND"

    def __init__(self):
        super().__init__("La compania no tiene una suscripcion activa configurada.")


class SubscriptionNotActiveError(PlanServiceError):
    code = "SUBSCRIPTION_NOT_ACTIVE"

    def __init__(self, status: str | None = None):
        self.status = status
        super().__init__("La suscripcion de la compania no esta activa.")


class PlanNotFoundError(PlanServiceError):
    code = "PLAN_NOT_FOUND"

    def __init__(self):
        super().__init__("Plan no encontrado.")


class PlanInactiveError(PlanServiceError):
    code = "PLAN_INACTIVE"

    def __init__(self):
        super().__init__("El plan asociado a la suscripcion no esta activo.")


class PlanCodeAlreadyExistsError(PlanServiceError):
    code = "PLAN_CODE_ALREADY_EXISTS"

    def __init__(self):
        super().__init__("Ya existe un plan con este codigo.")


class InvalidPlanPayloadError(PlanServiceError):
    code = "INVALID_PLAN_PAYLOAD"

    def __init__(self, message: str):
        super().__init__(message)


class FreePlanCannotBeDeactivatedError(PlanServiceError):
    code = "FREE_PLAN_CANNOT_BE_DEACTIVATED"

    def __init__(self):
        super().__init__("No se puede desactivar el plan free.")


class PlanHasActiveSubscriptionsError(PlanServiceError):
    code = "PLAN_HAS_ACTIVE_SUBSCRIPTIONS"

    def __init__(self):
        super().__init__("No se puede desactivar un plan con suscripciones activas.")
