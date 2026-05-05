import { apiClient } from "@/lib/api-client";

export async function getWebResource<TResponse>(path: `/api/web/${string}`) {
  const response = await apiClient.get<TResponse>(path);
  return response.data;
}

export async function postWebResource<TResponse, TPayload>(
  path: `/api/web/${string}`,
  payload: TPayload
) {
  const response = await apiClient.post<TResponse>(path, payload);
  return response.data;
}
