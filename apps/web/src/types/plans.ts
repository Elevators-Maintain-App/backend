export type PlanLimits = {
  admins: number | null;
  supervisors: number | null;
  technicians: number | null;
  projects: number | null;
  clients: number | null;
  units: number | null;
  work_orders_per_month: number | null;
  pdf_reports_per_month: number | null;
  storage_mb: number | null;
};

export type PlanFeatures = {
  offline_mode: boolean;
  custom_checklists: boolean;
  advanced_dashboard: boolean;
  evidence_editing: boolean;
};

export type Plan = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  is_public: boolean;
  is_active: boolean;
  limits?: PlanLimits | null;
  features?: PlanFeatures | null;
};

export type PlanCreateRequest = {
  code: string;
  name: string;
  description?: string | null;
  is_public: boolean;
  is_active: boolean;
  limits: PlanLimits;
  features: PlanFeatures;
};

export type PlanUpdateRequest = {
  code?: string;
  name?: string;
  description?: string | null;
  is_public?: boolean;
  is_active?: boolean;
  limits?: Partial<PlanLimits>;
  features?: Partial<PlanFeatures>;
};

export type CompanySubscription = {
  id: string;
  status: string;
  billing_period: string | null;
  start_date: string | null;
  end_date?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  trial_ends_at?: string | null;
  next_payment_due_at?: string | null;
};

export type CompanySubscriptionStatus = {
  company_id: string;
  subscription: CompanySubscription | null;
  plan: Plan | null;
  limits: PlanLimits;
  features: PlanFeatures;
  usage: {
    period_year: number;
    period_month: number;
    users_count: number;
    admins_count: number;
    supervisors_count: number;
    technicians_count: number;
    projects_count: number;
    clients_count: number;
    units_count: number;
    work_orders_created: number;
    pdf_reports_generated: number;
    storage_used_mb: number;
  };
};

export type PlanFormValues = {
  code: string;
  name: string;
  description: string;
  is_public: boolean;
  is_active: boolean;
  limits: PlanLimits;
  features: PlanFeatures;
};

export type AssignPlanPayload = {
  plan_id: string;
  status: string;
  billing_period: string;
  start_date: string;
  end_date?: string | null;
};

export type SuperAdminCompany = {
  id: string;
  name: string;
  email?: string | null;
  documento?: string | null;
};
