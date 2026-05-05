import { useQuery } from "@tanstack/react-query";
import {
  getSuperAdminUsers,
  getSuperAdminUsersSummary
} from "@/services/superadmin/users.service";
import type { SuperAdminUsersParams } from "@/types/superadmin";

export function useSuperAdminUsersSummary() {
  return useQuery({
    queryKey: ["superadmin", "users", "summary"],
    queryFn: getSuperAdminUsersSummary
  });
}

export function useSuperAdminUsers(params: SuperAdminUsersParams) {
  return useQuery({
    queryKey: ["superadmin", "users", params],
    queryFn: () => getSuperAdminUsers(params)
  });
}
