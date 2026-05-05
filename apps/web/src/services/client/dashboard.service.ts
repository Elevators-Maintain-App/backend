import { AxiosError } from "axios";
import { apiClient } from "@/lib/api-client";
import type { ClientDashboard } from "@/types/client-dashboard";

const clientDashboardPath = "/api/web/client/dashboard";

type ApiErrorPayload = {
  detail?: string;
};

export class ClientDashboardError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ClientDashboardError";
  }
}

export async function getClientDashboard() {
  try {
    const response = await apiClient.get<ClientDashboard>(clientDashboardPath);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      const detail = (error.response?.data as ApiErrorPayload | undefined)?.detail;
      throw new ClientDashboardError(detail || "No fue posible cargar el dashboard.");
    }
    throw error;
  }
}
