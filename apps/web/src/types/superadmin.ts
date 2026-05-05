export type SuperAdminUserRole =
  | "technician"
  | "supervisor"
  | "admin"
  | "superAdmin"
  | "client";

export type SuperAdminUsersSummary = {
  total_users: number;
};

export type SuperAdminUser = {
  uid: string;
  email: string;
  display_name: string;
  role: SuperAdminUserRole;
  company_id: string | null;
  company_name: string | null;
  photo_url: string | null;
  is_active: boolean;
};

export type SuperAdminUsersParams = {
  page: number;
  page_size: number;
  search?: string;
  role?: SuperAdminUserRole;
};

export type SuperAdminUsersPage = {
  data: SuperAdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

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
