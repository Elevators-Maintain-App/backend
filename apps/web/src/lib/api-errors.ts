import axios from "axios";

type ApiErrorDetail = {
  message?: string;
  detail?: string;
  code?: string;
};

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string | ApiErrorDetail } | undefined;
    const detail = data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return detail.code ? `${detail.message} (${detail.code})` : detail.message;
    }

    if (detail?.detail) {
      return detail.code ? `${detail.detail} (${detail.code})` : detail.detail;
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

  return "Ocurrio un error inesperado.";
}
