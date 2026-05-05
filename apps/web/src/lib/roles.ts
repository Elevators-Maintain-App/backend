import type { NormalizedUserRole } from "@/types/auth";

const roleMap: Record<string, NormalizedUserRole> = {
  admin: "admin",
  client: "client",
  cliente: "client",
  superadmin: "superadmin",
  super_admin: "superadmin",
  supervisor: "supervisor",
  technician: "technician",
  tecnico: "technician"
};

const dashboardRouteMap: Record<NormalizedUserRole, string> = {
  admin: "/dashboard/admin",
  client: "/dashboard/client",
  superadmin: "/dashboard/superadmin",
  supervisor: "/dashboard/supervisor",
  technician: "/dashboard/technician"
};

export function normalizeUserRole(role: unknown): NormalizedUserRole | null {
  if (typeof role !== "string") {
    return null;
  }

  const normalizedInput = role.trim().toLowerCase();
  return roleMap[normalizedInput] || null;
}

export function getDashboardRouteForRole(role: NormalizedUserRole) {
  return dashboardRouteMap[role];
}
