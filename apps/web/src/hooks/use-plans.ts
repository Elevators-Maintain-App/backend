import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignCompanyPlan,
  createAdminPlan,
  deactivateAdminPlan,
  getAdminPlan,
  getCompanySubscription,
  listAdminPlans,
  listSuperAdminCompaniesForPlans,
  updateAdminPlan,
} from "@/services/plans.service";
import type { AssignPlanPayload, PlanFormValues, SuperAdminCompany } from "@/types/plans";

export function useAdminPlans(includeInactive = true) {
  return useQuery({
    queryKey: ["admin", "plans", { includeInactive }],
    queryFn: () => listAdminPlans(includeInactive),
  });
}

export function useAdminPlanDetail(planId?: string) {
  return useQuery({
    queryKey: ["admin", "plans", planId],
    queryFn: () => getAdminPlan(planId || ""),
    enabled: Boolean(planId),
  });
}

export function useCreateAdminPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (values: PlanFormValues) => createAdminPlan(values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
    },
  });
}

export function useUpdateAdminPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ planId, values }: { planId: string; values: PlanFormValues }) =>
      updateAdminPlan(planId, values),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
      await queryClient.invalidateQueries({ queryKey: ["admin", "company-subscription"] });
    },
  });
}

export function useDeactivateAdminPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (planId: string) => deactivateAdminPlan(planId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
      await queryClient.invalidateQueries({ queryKey: ["admin", "company-subscription"] });
    },
  });
}

export function useSuperAdminCompaniesForPlans() {
  return useQuery({
    queryKey: ["admin", "companies", "plans"],
    queryFn: listSuperAdminCompaniesForPlans,
  });
}

export function useCompanySubscription(companyId?: string) {
  return useQuery({
    queryKey: ["admin", "company-subscription", companyId],
    queryFn: () => getCompanySubscription(companyId || ""),
    enabled: Boolean(companyId),
  });
}

export function useCompanySubscriptionStatuses(companies: SuperAdminCompany[]) {
  return useQueries({
    queries: companies.map((company) => ({
      queryKey: ["admin", "company-subscription", company.id],
      queryFn: () => getCompanySubscription(company.id),
      enabled: Boolean(company.id),
      retry: false,
    })),
  });
}

export function useAssignCompanyPlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ companyId, payload }: { companyId: string; payload: AssignPlanPayload }) =>
      assignCompanyPlan(companyId, payload),
    onSuccess: async (_status, variables) => {
      queryClient.setQueryData(
        ["admin", "company-subscription", variables.companyId],
        _status
      );
      await queryClient.invalidateQueries({
        queryKey: ["admin", "company-subscription", variables.companyId],
      });
    },
  });
}
