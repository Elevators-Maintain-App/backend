import axios from "axios";

type ApiErrorDetail = {
  message?: string;
  detail?: string;
  code?: string;
  resource?: string;
  current_usage?: number;
  plan_limit?: number | null;
};

const PLAN_RESOURCE_LABELS: Record<string, string> = {
  admins: "administradores",
  supervisors: "supervisores",
  technicians: "técnicos",
  clients: "clientes",
  projects: "proyectos",
  units: "unidades",
  work_orders_per_month: "órdenes de trabajo mensuales",
  pdf_reports_per_month: "reportes PDF mensuales",
  storage_mb: "almacenamiento",
};

const API_CODE_MESSAGES: Record<string, string> = {
  PLAN_HAS_ACTIVE_SUBSCRIPTIONS:
    "No se puede desactivar este plan porque tiene compañías activas asignadas.",
  FREE_PLAN_CANNOT_BE_DEACTIVATED: "El plan free no se puede desactivar.",
};

function formatMessage(message: string, code?: string) {
  return code ? `${message} (${code})` : message;
}

export function getApiErrorDetail(error: unknown): string | ApiErrorDetail | null {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | ApiErrorDetail; message?: string; code?: string }
      | string
      | undefined;

    if (typeof data === "string") {
      return data;
    }

    if (data?.detail) {
      return data.detail;
    }

    if (data?.message || data?.code) {
      return {
        message: data.message,
        code: data.code,
      };
    }
  }

  if (typeof error === "object" && error !== null) {
    const candidate = error as { detail?: unknown; message?: unknown; code?: unknown };
    if (typeof candidate.detail === "string") {
      return candidate.detail;
    }
    if (typeof candidate.detail === "object" && candidate.detail !== null) {
      return candidate.detail as ApiErrorDetail;
    }
    if (typeof candidate.message === "string" || typeof candidate.code === "string") {
      return {
        message: typeof candidate.message === "string" ? candidate.message : undefined,
        code: typeof candidate.code === "string" ? candidate.code : undefined,
      };
    }
  }

  return null;
}

export function isPlanLimitReachedError(error: unknown) {
  const detail = getApiErrorDetail(error);
  return typeof detail === "object" && detail?.code === "PLAN_LIMIT_REACHED";
}

export function getPlanLimitReachedMessage(error: unknown) {
  const detail = getApiErrorDetail(error);

  if (typeof detail !== "object" || detail?.code !== "PLAN_LIMIT_REACHED") {
    return null;
  }

  const resourceLabel = detail.resource
    ? PLAN_RESOURCE_LABELS[detail.resource] || detail.resource
    : null;

  if (
    resourceLabel &&
    typeof detail.current_usage === "number" &&
    (typeof detail.plan_limit === "number" || detail.plan_limit === null)
  ) {
    const limitText = detail.plan_limit === null ? "sin límite" : String(detail.plan_limit);
    return [
      `No se pudo crear el usuario porque la compañía alcanzó el límite de ${resourceLabel} de su plan.`,
      `Uso actual: ${detail.current_usage} / ${limitText}.`,
      "Cambia el plan de la compañía o aumenta el límite para continuar.",
    ].join("\n");
  }

  return detail.message || "La compañía alcanzó un límite de su plan.";
}

export function getApiErrorMessage(error: unknown): string {
  const planLimitMessage = getPlanLimitReachedMessage(error);
  if (planLimitMessage) {
    return planLimitMessage;
  }

  if (axios.isAxiosError(error)) {
    const detail = getApiErrorDetail(error);

    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      if (detail.code && API_CODE_MESSAGES[detail.code]) {
        return API_CODE_MESSAGES[detail.code];
      }
      return formatMessage(detail.message, detail.code);
    }

    if (detail?.detail) {
      if (detail.code && API_CODE_MESSAGES[detail.code]) {
        return API_CODE_MESSAGES[detail.code];
      }
      return formatMessage(detail.detail, detail.code);
    }

    const data = error.response?.data as { message?: string; code?: string } | undefined;
    if (data?.message) {
      if (data.code && API_CODE_MESSAGES[data.code]) {
        return API_CODE_MESSAGES[data.code];
      }
      return formatMessage(data.message, data.code);
    }

    if (error.response?.status === 404) {
      return "El recurso solicitado no existe o el endpoint todavia no esta disponible.";
    }

    if (error.response?.status === 405) {
      return "Esta accion todavia no esta soportada por el backend.";
    }

    if (error.message) {
      return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "object" && error !== null) {
    const candidate = error as { message?: unknown; detail?: unknown };
    if (typeof candidate.message === "string") {
      return candidate.message;
    }
    if (typeof candidate.detail === "string") {
      return candidate.detail;
    }
  }

  return "Ocurrio un error inesperado.";
}
