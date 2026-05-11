import { apiClient } from "@/lib/api-client";
import { listSuperadminUsers } from "@/services/superadmin-users-service";
import type {
  CreateSuperAdminUserInput,
  SuperAdminCatalogItem,
  SuperAdminUser,
  SuperAdminUsersPage,
  SuperAdminUsersParams,
  SuperAdminUsersSummary
} from "@/types/superadmin";

const superAdminUsersBasePath = "/api/web/superadmin/users";
const superAdminBasePath = "/api/web/superadmin";

export async function getSuperAdminUsersSummary() {
  const response = await apiClient.get<SuperAdminUsersSummary>(
    `${superAdminUsersBasePath}/summary`
  );
  return response.data;
}

export async function getSuperAdminUsers(params: SuperAdminUsersParams) {
  return listSuperadminUsers(params) as Promise<SuperAdminUsersPage>;
}

export async function getSuperAdminCompanies() {
  const response = await apiClient.get<SuperAdminCatalogItem[]>(
    `${superAdminBasePath}/catalogs/companies`
  );
  return response.data;
}

export async function getSuperAdminDocumentTypes() {
  const response = await apiClient.get<SuperAdminCatalogItem[]>(
    `${superAdminBasePath}/catalogs/document-types`
  );
  return response.data;
}

export async function getSuperAdminTechnicalLevels(companyId?: string) {
  const searchParams = new URLSearchParams();
  if (companyId) {
    searchParams.set("company_id", companyId);
  }

  const queryString = searchParams.toString();
  const response = await apiClient.get<SuperAdminCatalogItem[]>(
    `${superAdminBasePath}/catalogs/technical-levels${queryString ? `?${queryString}` : ""}`
  );
  return response.data;
}

export async function getSuperAdminCompanyClients(companyId: string) {
  const response = await apiClient.get<SuperAdminCatalogItem[]>(
    `${superAdminBasePath}/companies/${companyId}/clients`
  );
  return response.data;
}

export async function createSuperAdminUser(input: CreateSuperAdminUserInput) {
  const formData = new FormData();
  formData.set("company_id", input.company_id);
  formData.set("display_name", input.display_name);
  formData.set("document_id", input.document_id);
  formData.set("document_type_id", String(input.document_type_id));
  formData.set("email", input.email);
  formData.set("phone_number", input.phone_number);
  formData.set("rol", input.rol);
  formData.set("is_active", String(input.is_active ?? true));

  if (input.rol === "client" && input.client_id) {
    formData.set("client_id", input.client_id);
  }

  if (input.rol === "technician" && input.nivel) {
    formData.set("nivel", input.nivel);
  }

  const response = await apiClient.post<SuperAdminUser>(
    superAdminUsersBasePath,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );
  return response.data;
}
