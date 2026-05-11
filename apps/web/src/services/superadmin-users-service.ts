import { apiClient } from "@/lib/api-client";
import type {
  CreateSuperadminUserInput,
  SuperadminUserDetail,
  SuperadminUserDeleteResponse,
  SuperadminUserDisableResponse,
  SuperadminUsersListParams,
  SuperadminUsersListResponse,
  UpdateSuperadminUserInput,
} from "@/types/superadmin-users";

const superadminUsersPath = "/api/web/superadmin/users";

export async function listSuperadminUsers(
  params: SuperadminUsersListParams
) {
  const searchParams = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size),
  });

  if (params.search) {
    searchParams.set("search", params.search);
  }

  if (params.role) {
    searchParams.set("role", params.role);
  }

  if (params.company_id) {
    searchParams.set("company_id", params.company_id);
  }

  if (params.status) {
    searchParams.set("status", params.status);
  }

  const response = await apiClient.get<SuperadminUsersListResponse>(
    `${superadminUsersPath}?${searchParams.toString()}`
  );
  const items = response.data.items || response.data.data || [];

  return {
    ...response.data,
    items,
    data: response.data.data || items,
  };
}

export async function getSuperadminUser(userId: string) {
  const response = await apiClient.get<SuperadminUserDetail>(
    `${superadminUsersPath}/${userId}`
  );
  return response.data;
}

export async function createSuperadminUser(payload: CreateSuperadminUserInput) {
  const response = await apiClient.post<SuperadminUserDetail>(
    superadminUsersPath,
    payload
  );
  return response.data;
}

export async function updateSuperadminUser(
  userId: string,
  payload: UpdateSuperadminUserInput
) {
  const response = await apiClient.patch<SuperadminUserDetail>(
    `${superadminUsersPath}/${userId}`,
    payload
  );
  return response.data;
}

export async function disableSuperadminUser(userId: string) {
  const response = await apiClient.post<SuperadminUserDisableResponse>(
    `${superadminUsersPath}/${userId}/disable`
  );
  return response.data;
}

export async function deleteSuperadminUser(userId: string) {
  const response = await apiClient.delete<SuperadminUserDeleteResponse>(
    `${superadminUsersPath}/${userId}`
  );
  return response.data;
}
