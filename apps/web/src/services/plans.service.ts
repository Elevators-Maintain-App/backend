import { apiClient } from "@/lib/api-client";
import type {
  AssignPlanPayload,
  CompanySubscriptionStatus,
  Plan,
  PlanFormValues,
  PlanUpsertPayload,
  SuperAdminCompany,
} from "@/types/plans";
import type { SuperAdminCatalogItem } from "@/types/superadmin";

function toPlanPayload(values: PlanFormValues): PlanUpsertPayload {
  return {
    code: values.code.trim(),
    name: values.name.trim(),
    description: values.description.trim() || null,
    max_admins: values.limits.admins,
    max_supervisors: values.limits.supervisors,
    max_technicians: values.limits.technicians,
    max_projects: values.limits.projects,
    max_clients: values.limits.clients,
    max_units: values.limits.units,
    max_work_orders_per_month: values.limits.work_orders_per_month,
    max_pdf_reports_per_month: values.limits.pdf_reports_per_month,
    storage_limit_mb: values.limits.storage_mb,
    allow_offline_mode: values.features.offline_mode,
    allow_custom_checklists: values.features.custom_checklists,
    allow_advanced_dashboard: values.features.advanced_dashboard,
    allow_evidence_editing: values.features.evidence_editing,
    is_public: values.is_public,
    is_active: values.is_active,
  };
}

export async function listAdminPlans(includeInactive = true) {
  const response = await apiClient.get<Plan[]>(
    `/api/admin/plans?include_inactive=${String(includeInactive)}`
  );
  return response.data;
}

export async function createAdminPlan(values: PlanFormValues) {
  const response = await apiClient.post<Plan>("/api/admin/plans", toPlanPayload(values));
  return response.data;
}

export async function updateAdminPlan(planId: string, values: PlanFormValues) {
  const response = await apiClient.patch<Plan>(
    `/api/admin/plans/${planId}`,
    toPlanPayload(values)
  );
  return response.data;
}

export async function deactivateAdminPlan(planId: string) {
  const response = await apiClient.patch<Plan>(`/api/admin/plans/${planId}`, {
    is_active: false,
  });
  return response.data;
}

export async function deleteAdminPlan(planId: string) {
  const response = await apiClient.delete<{ deleted: boolean } | Plan>(
    `/api/admin/plans/${planId}`
  );
  return response.data;
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
