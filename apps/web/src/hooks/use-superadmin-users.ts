import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSuperAdminUser,
  getSuperAdminCompanies,
  getSuperAdminCompanyClients,
  getSuperAdminDocumentTypes,
  getSuperAdminTechnicalLevels,
  getSuperAdminUsers,
  getSuperAdminUsersSummary
} from "@/services/superadmin/users.service";
import type {
  CreateSuperAdminUserInput,
  SuperAdminUsersParams
} from "@/types/superadmin";

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

export function useSuperAdminCompanies() {
  return useQuery({
    queryKey: ["superadmin", "catalogs", "companies"],
    queryFn: getSuperAdminCompanies
  });
}

export function useSuperAdminDocumentTypes() {
  return useQuery({
    queryKey: ["superadmin", "catalogs", "document-types"],
    queryFn: getSuperAdminDocumentTypes
  });
}

export function useSuperAdminTechnicalLevels(companyId?: string) {
  return useQuery({
    queryKey: ["superadmin", "catalogs", "technical-levels", companyId],
    queryFn: () => getSuperAdminTechnicalLevels(companyId),
    enabled: Boolean(companyId)
  });
}

export function useSuperAdminCompanyClients(companyId?: string) {
  return useQuery({
    queryKey: ["superadmin", "companies", companyId, "clients"],
    queryFn: () => getSuperAdminCompanyClients(companyId || ""),
    enabled: Boolean(companyId)
  });
}

export function useCreateSuperAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateSuperAdminUserInput) => createSuperAdminUser(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["superadmin", "users"]
      });
    }
  });
}
