PLAN_LIMIT_REACHED_CODE = "PLAN_LIMIT_REACHED"
PLAN_FEATURE_NOT_ALLOWED_CODE = "PLAN_FEATURE_NOT_ALLOWED"
SUBSCRIPTION_NOT_FOUND_CODE = "SUBSCRIPTION_NOT_FOUND"
SUBSCRIPTION_NOT_ACTIVE_CODE = "SUBSCRIPTION_NOT_ACTIVE"
PLAN_NOT_FOUND_CODE = "PLAN_NOT_FOUND"
PLAN_INACTIVE_CODE = "PLAN_INACTIVE"
INVALID_PLAN_RESOURCE_CODE = "INVALID_PLAN_RESOURCE"
INVALID_PLAN_FEATURE_CODE = "INVALID_PLAN_FEATURE"

ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active", "trial", "trialing"})

RESOURCE_LIMIT_FIELDS = {
    "admins": "max_admins",
    "supervisors": "max_supervisors",
    "technicians": "max_technicians",
    "projects": "max_projects",
    "clients": "max_clients",
    "units": "max_units",
    "work_orders_per_month": "max_work_orders_per_month",
    "pdf_reports_per_month": "max_pdf_reports_per_month",
    "storage_mb": "storage_limit_mb",
}

RESOURCE_LABELS = {
    "admins": "administradores",
    "supervisors": "supervisores",
    "technicians": "tecnicos",
    "projects": "proyectos",
    "clients": "clientes",
    "units": "unidades",
    "work_orders_per_month": "ordenes de trabajo mensuales",
    "pdf_reports_per_month": "reportes PDF mensuales",
    "storage_mb": "almacenamiento",
}

FEATURE_FIELDS = {
    "offline_mode": "allow_offline_mode",
    "custom_checklists": "allow_custom_checklists",
    "advanced_dashboard": "allow_advanced_dashboard",
    "evidence_editing": "allow_evidence_editing",
}
