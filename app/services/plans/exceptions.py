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
        super().__init__("No se encontro el plan asociado a la suscripcion.")


class PlanInactiveError(PlanServiceError):
    code = "PLAN_INACTIVE"

    def __init__(self):
        super().__init__("El plan asociado a la suscripcion no esta activo.")
