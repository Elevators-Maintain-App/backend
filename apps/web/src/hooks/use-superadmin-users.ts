import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSuperadminUser,
  deleteSuperadminUser,
  disableSuperadminUser,
  getSuperadminUser,
  listSuperadminUsers,
  updateSuperadminUser
} from "@/services/superadmin-users-service";
import {
  createSuperAdminUser,
  getSuperAdminCompanies,
  getSuperAdminCompanyClients,
  getSuperAdminDocumentTypes,
  getSuperAdminTechnicalLevels,
  getSuperAdminUsersSummary
} from "@/services/superadmin/users.service";
import type {
  CreateSuperAdminUserInput,
  SuperAdminUsersParams
} from "@/types/superadmin";
import type {
  CreateSuperadminUserInput,
  UpdateSuperadminUserInput
} from "@/types/superadmin-users";

export function useSuperAdminUsersSummary() {
  return useQuery({
    queryKey: ["superadmin", "users", "summary"],
    queryFn: getSuperAdminUsersSummary
  });
}

export function useSuperAdminUsers(params: SuperAdminUsersParams) {
  return useQuery({
    queryKey: ["superadmin", "users", params],
    queryFn: () => listSuperadminUsers(params)
  });
}

export function useSuperadminUsers(params: SuperAdminUsersParams) {
  return useSuperAdminUsers(params);
}

export function useSuperadminUser(userId?: string) {
  return useQuery({
    queryKey: ["superadmin", "users", "detail", userId],
    queryFn: () => getSuperadminUser(userId || ""),
    enabled: Boolean(userId)
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

export function useCreateSuperadminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateSuperadminUserInput) => createSuperadminUser(input),
    onSuccess: async (user) => {
      if (user?.uid) {
        queryClient.setQueryData(
          ["superadmin", "users", "detail", user.uid],
          user
        );
      }

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users"]
        }),
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users", "summary"]
        })
      ]);
    }
  });
}

export function useUpdateSuperadminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      uid,
      payload
    }: {
      uid: string;
      payload: UpdateSuperadminUserInput;
    }) => updateSuperadminUser(uid, payload),
    onSuccess: async (user, variables) => {
      queryClient.setQueryData(
        ["superadmin", "users", "detail", variables.uid],
        user
      );

      await queryClient.invalidateQueries({
        queryKey: ["superadmin", "users"]
      });
    }
  });
}

export function useDisableSuperadminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (uid: string) => disableSuperadminUser(uid),
    onSuccess: async (_response, uid) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users"]
        }),
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users", "detail", uid]
        })
      ]);
    }
  });
}

export function useDeleteSuperadminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (uid: string) => deleteSuperadminUser(uid),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users"]
        }),
        queryClient.invalidateQueries({
          queryKey: ["superadmin", "users", "summary"]
        })
      ]);
    }
  });
}
