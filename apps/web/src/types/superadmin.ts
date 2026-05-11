import type {
  SuperadminUserListItem,
  SuperadminUserRole,
  SuperadminUsersListParams,
  SuperadminUsersListResponse,
} from "@/types/superadmin-users";

export type SuperAdminUserRole = SuperadminUserRole;

export type SuperAdminUsersSummary = {
  total_users: number;
};

export type SuperAdminUser = SuperadminUserListItem;

export type SuperAdminUsersParams = SuperadminUsersListParams;

export type SuperAdminUsersPage = SuperadminUsersListResponse;

export type SuperAdminCatalogItem = {
  id: string;
  name: string;
};

export type CreateSuperAdminUserInput = {
  company_id: string;
  display_name: string;
  document_id: string;
  document_type_id: number;
  email: string;
  phone_number: string;
  rol: SuperAdminUserRole;
  client_id?: string;
  nivel?: string;
  is_active?: boolean;
};
