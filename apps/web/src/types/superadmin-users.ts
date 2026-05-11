export type SuperadminUserRole =
  | "technician"
  | "supervisor"
  | "admin"
  | "superAdmin"
  | "client";

export type SuperadminUserStatus = "active" | "inactive" | "unknown";

export type SuperadminUsersListParams = {
  page: number;
  page_size: number;
  search?: string;
  role?: SuperadminUserRole;
  company_id?: string;
  status?: SuperadminUserStatus;
};

export type SuperadminUserListItem = {
  uid: string;
  display_name: string;
  email: string;
  phone: string | null;
  role: SuperadminUserRole;
  company_id: string | null;
  company_name: string | null;
  photo_url?: string | null;
  is_active?: boolean | null;
  status: SuperadminUserStatus;
  created_at: string | null;
  updated_at: string | null;
};

export type SuperadminUsersListResponse = {
  items: SuperadminUserListItem[];
  data: SuperadminUserListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type SuperadminUserDetail = SuperadminUserListItem & {
  id: string | null;
  phone_number: string | null;
  photo_url: string | null;
  is_active: boolean | null;
  document_id: string | null;
  document_type_id: number | null;
  document_type_name: string | null;
  client_id: string | null;
  nivel: string | null;
};

export type CreateSuperadminUserInput = {
  display_name: string;
  email: string;
  phone?: string | null;
  role: SuperadminUserRole;
  company_id?: string | null;
  password?: string | null;
};

export type UpdateSuperadminUserInput = {
  display_name?: string | null;
  phone?: string | null;
  role?: SuperadminUserRole | null;
  company_id?: string | null;
  status?: Extract<SuperadminUserStatus, "active" | "inactive"> | null;
};

export type SuperadminUserDisableResponse = {
  uid: string;
  status: Extract<SuperadminUserStatus, "active" | "inactive">;
  message?: string;
};

export type SuperadminUserDeleteResponse = {
  uid: string;
  deleted: boolean;
  message?: string;
};
