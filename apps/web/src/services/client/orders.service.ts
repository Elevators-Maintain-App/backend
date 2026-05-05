import { apiClient } from "@/lib/api-client";
import type {
  ClientOrder,
  ClientOrderDetail,
  ClientOrdersParams,
  ClientPage,
  ClientReportLink
} from "@/types/client-portal";

const clientOrdersPath = "/api/web/client/orders";

function buildOrderSearchParams(params: ClientOrdersParams) {
  const searchParams = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size)
  });

  if (params.search) {
    searchParams.set("search", params.search);
  }
  if (params.status) {
    searchParams.set("status", params.status);
  }
  if (params.unit_id) {
    searchParams.set("unit_id", params.unit_id);
  }
  if (params.project_id) {
    searchParams.set("project_id", params.project_id);
  }

  return searchParams.toString();
}

export async function getClientOrders(params: ClientOrdersParams) {
  const response = await apiClient.get<ClientPage<ClientOrder>>(
    `${clientOrdersPath}?${buildOrderSearchParams(params)}`
  );
  return response.data;
}

export async function getClientOrderDetail(orderId: string) {
  const response = await apiClient.get<ClientOrderDetail>(
    `${clientOrdersPath}/${orderId}`
  );
  return response.data;
}

export async function getClientOrderReport(orderId: string) {
  const response = await apiClient.get<ClientReportLink>(
    `${clientOrdersPath}/${orderId}/report`
  );
  return response.data;
}
