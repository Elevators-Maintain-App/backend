import axios from "axios";

type ApiErrorDetail = {
  message?: string;
  detail?: string;
  code?: string;
};

function formatMessage(message: string, code?: string) {
  return code ? `${message} (${code})` : message;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | ApiErrorDetail; message?: string; code?: string }
      | string
      | undefined;

    if (typeof data === "string") {
      return data;
    }

    const detail = data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return formatMessage(detail.message, detail.code);
    }

    if (detail?.detail) {
      return formatMessage(detail.detail, detail.code);
    }

    if (data?.message) {
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
