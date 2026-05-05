import { apiClient } from "@/lib/api-client";
import type {
  SuperAdminUsersPage,
  SuperAdminUsersParams,
  SuperAdminUsersSummary
} from "@/types/superadmin";

const superAdminUsersBasePath = "/api/web/superadmin/users";

export async function getSuperAdminUsersSummary() {
  const response = await apiClient.get<SuperAdminUsersSummary>(
    `${superAdminUsersBasePath}/summary`
  );
  return response.data;
}

export async function getSuperAdminUsers(params: SuperAdminUsersParams) {
  const searchParams = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.page_size)
  });

  if (params.search) {
    searchParams.set("search", params.search);
  }

  if (params.role) {
    searchParams.set("role", params.role);
  }

  const response = await apiClient.get<SuperAdminUsersPage>(
    `${superAdminUsersBasePath}?${searchParams.toString()}`
  );
  return response.data;
}
