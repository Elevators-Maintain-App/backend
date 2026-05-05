export type UserRole =
  | "client"
  | "cliente"
  | "technician"
  | "tecnico"
  | "supervisor"
  | "admin"
  | "superAdmin"
  | "super_admin";

export type NormalizedUserRole =
  | "client"
  | "technician"
  | "supervisor"
  | "admin"
  | "superadmin";

export type UserProfile = {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoUrl: string | null;
  role: NormalizedUserRole | null;
  rawRole: string | null;
};
