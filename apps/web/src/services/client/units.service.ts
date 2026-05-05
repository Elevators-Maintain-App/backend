import { apiClient } from "@/lib/api-client";
import type {
  ClientPage,
  ClientUnit,
  ClientUnitDetail,
  ClientUnitsParams
} from "@/types/client-portal";

const clientUnitsPath = "/api/web/client/units";

function buildUnitSearchParams(params: ClientUnitsParams) {
  const searchParams = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size)
  });

  if (params.search) {
    searchParams.set("search", params.search);
  }
  if (params.project_id) {
    searchParams.set("project_id", params.project_id);
  }

  return searchParams.toString();
}

export async function getClientUnits(params: ClientUnitsParams) {
  const response = await apiClient.get<ClientPage<ClientUnit>>(
    `${clientUnitsPath}?${buildUnitSearchParams(params)}`
  );
  return response.data;
}

export async function getClientUnitDetail(unitId: string) {
  const response = await apiClient.get<ClientUnitDetail>(
    `${clientUnitsPath}/${unitId}`
  );
  return response.data;
}
