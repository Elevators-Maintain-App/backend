import { apiClient } from "@/lib/api-client";
import type {
  AssignPlanPayload,
  CompanySubscriptionStatus,
  Plan,
  PlanCreateRequest,
  PlanFeatures,
  PlanFormValues,
  PlanLimits,
  PlanUpdateRequest,
  SuperAdminCompany,
} from "@/types/plans";
import type { SuperAdminCatalogItem } from "@/types/superadmin";

const emptyLimits: PlanLimits = {
  admins: null,
  supervisors: null,
  technicians: null,
  projects: null,
  clients: null,
  units: null,
  work_orders_per_month: null,
  pdf_reports_per_month: null,
  storage_mb: null,
};

const emptyFeatures: PlanFeatures = {
  offline_mode: false,
  custom_checklists: false,
  advanced_dashboard: false,
  evidence_editing: false,
};

function normalizePlan(plan: Plan): Plan {
  return {
    ...plan,
    limits: {
      ...emptyLimits,
      ...(plan.limits || {}),
    },
    features: {
      ...emptyFeatures,
      ...(plan.features || {}),
    },
  };
}

function normalizeCode(code: string) {
  return code.trim().toLowerCase().replace(/\s+/g, "_");
}

function toPlanCreatePayload(values: PlanFormValues): PlanCreateRequest {
  return {
    code: normalizeCode(values.code),
    name: values.name.trim(),
    description: values.description.trim() || null,
    is_public: values.is_public,
    is_active: values.is_active,
    limits: values.limits,
    features: values.features,
  };
}

function toPlanUpdatePayload(values: PlanFormValues): PlanUpdateRequest {
  return toPlanCreatePayload(values);
}

export async function listAdminPlans(includeInactive = true) {
  const response = await apiClient.get<Plan[]>(
    `/api/admin/plans?include_inactive=${String(includeInactive)}`
  );
  return response.data.map(normalizePlan);
}

export async function getAdminPlan(planId: string) {
  const response = await apiClient.get<Plan>(`/api/admin/plans/${planId}`);
  return normalizePlan(response.data);
}

export async function createAdminPlan(values: PlanFormValues) {
  const response = await apiClient.post<Plan>("/api/admin/plans", toPlanCreatePayload(values));
  return normalizePlan(response.data);
}

export async function updateAdminPlan(planId: string, values: PlanFormValues) {
  const response = await apiClient.patch<Plan>(
    `/api/admin/plans/${planId}`,
    toPlanUpdatePayload(values)
  );
  return normalizePlan(response.data);
}

export async function deactivateAdminPlan(planId: string) {
  const response = await apiClient.patch<Plan>(
    `/api/admin/plans/${planId}/deactivate`
  );
  return normalizePlan(response.data);
}

export async function listSuperAdminCompaniesForPlans(): Promise<SuperAdminCompany[]> {
  const response = await apiClient.get<SuperAdminCatalogItem[]>(
    "/api/web/superadmin/catalogs/companies"
  );

  return response.data.map((company) => ({
    id: company.id,
    name: company.name,
  }));
}

export async function getCompanySubscription(companyId: string) {
  const response = await apiClient.get<CompanySubscriptionStatus>(
    `/api/admin/companies/${companyId}/subscription`
  );
  return response.data;
}

export async function assignCompanyPlan(companyId: string, payload: AssignPlanPayload) {
  const response = await apiClient.post<CompanySubscriptionStatus>(
    `/api/admin/companies/${companyId}/subscription`,
    payload
  );
  return response.data;
}
