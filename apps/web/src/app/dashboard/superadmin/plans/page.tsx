"use client";

import { Edit3, Eye, ExternalLink, Plus, Power, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { PlanForm, formatLimit } from "@/components/plans/plan-form";
import { PlanModal } from "@/components/plans/plan-modal";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import { getApiErrorMessage } from "@/lib/api-errors";
import {
  useAdminPlans,
  useAdminPlanDetail,
  useCreateAdminPlan,
  useDeactivateAdminPlan,
  useUpdateAdminPlan,
} from "@/hooks/use-plans";
import type { Plan, PlanFeatures, PlanFormValues, PlanLimits } from "@/types/plans";

function planTone(plan: Plan) {
  return plan.is_active ? "success" : "danger";
}

function publicTone(plan: Plan) {
  return plan.is_public ? "info" : "neutral";
}

function featuresSummary(plan: Plan) {
  const features = plan.features || {
    offline_mode: false,
    custom_checklists: false,
    advanced_dashboard: false,
    evidence_editing: false,
  };

  return [
    features.offline_mode ? "Offline" : null,
    features.custom_checklists ? "Checklists" : null,
    features.advanced_dashboard ? "Dashboard" : null,
    features.evidence_editing ? "Evidencias" : null,
  ].filter(Boolean).join(", ") || "Sin features";
}

function formatStorage(value: number | null | undefined) {
  return value === null || value === undefined ? "Sin límite" : `${value} MB`;
}

const detailLimitLabels: Array<{ key: keyof PlanLimits; label: string }> = [
  { key: "admins", label: "Admins" },
  { key: "supervisors", label: "Supervisores" },
  { key: "technicians", label: "Técnicos" },
  { key: "projects", label: "Proyectos" },
  { key: "clients", label: "Clientes" },
  { key: "units", label: "Unidades" },
  { key: "work_orders_per_month", label: "Órdenes/mes" },
  { key: "pdf_reports_per_month", label: "PDFs/mes" },
  { key: "storage_mb", label: "Storage MB" },
];

const detailFeatureLabels: Array<{ key: keyof PlanFeatures; label: string }> = [
  { key: "offline_mode", label: "Modo offline" },
  { key: "custom_checklists", label: "Checklists personalizados" },
  { key: "advanced_dashboard", label: "Dashboard avanzado" },
  { key: "evidence_editing", label: "Edición de evidencias" },
];

export default function SuperAdminPlansPage() {
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [detailPlanId, setDetailPlanId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const plansQuery = useAdminPlans(true);
  const createPlan = useCreateAdminPlan();
  const updatePlan = useUpdateAdminPlan();
  const deactivatePlan = useDeactivateAdminPlan();
  const detailPlanQuery = useAdminPlanDetail(detailPlanId || undefined);

  const plans = plansQuery.data || [];
  const detailPlan = detailPlanQuery.data || null;
  const isPlanFormOpen = isCreating || Boolean(editingPlan);

  const handleSubmit = async (values: PlanFormValues) => {
    setActionError(null);
    setSuccessMessage(null);

    try {
      if (editingPlan) {
        await updatePlan.mutateAsync({ planId: editingPlan.id, values });
        setSuccessMessage("Plan actualizado correctamente.");
      } else {
        await createPlan.mutateAsync(values);
        setSuccessMessage("Plan creado correctamente.");
      }
      setEditingPlan(null);
      setIsCreating(false);
      setDetailPlanId(null);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  };

  const handleDeactivate = async (plan: Plan) => {
    const confirmed = window.confirm(`¿Desactivar el plan "${plan.name}"?`);
    if (!confirmed) {
      return;
    }

    setActionError(null);
    setSuccessMessage(null);
    try {
      await deactivatePlan.mutateAsync(plan.id);
      setSuccessMessage("Plan desactivado correctamente.");
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  };

  const columns = [
    {
      key: "plan",
      header: "Plan",
      cell: (plan: Plan) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{plan.name}</p>
          <p className="truncate text-xs text-muted-foreground">{plan.code}</p>
        </div>
      ),
    },
    {
      key: "status",
      header: "Estado",
      cell: (plan: Plan) => (
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone={planTone(plan)}>
            {plan.is_active ? "Activo" : "Inactivo"}
          </StatusBadge>
          <StatusBadge tone={publicTone(plan)}>
            {plan.is_public ? "Público" : "Privado"}
          </StatusBadge>
        </div>
      ),
    },
    {
      key: "limits",
      header: "Límites clave",
      cell: (plan: Plan) => (
        <div className="space-y-1 text-xs text-muted-foreground">
          <p>Técnicos: {formatLimit(plan.limits?.technicians)}</p>
          <p>Proyectos: {formatLimit(plan.limits?.projects)}</p>
          <p>Unidades: {formatLimit(plan.limits?.units)}</p>
          <p>Órdenes/mes: {formatLimit(plan.limits?.work_orders_per_month)}</p>
          <p>PDFs/mes: {formatLimit(plan.limits?.pdf_reports_per_month)}</p>
          <p>Storage: {formatStorage(plan.limits?.storage_mb)}</p>
        </div>
      ),
    },
    {
      key: "features",
      header: "Features",
      cell: (plan: Plan) => (
        <span className="text-sm text-muted-foreground">{featuresSummary(plan)}</span>
      ),
    },
    {
      key: "actions",
      header: "Acciones",
      cell: (plan: Plan) => (
        <div className="flex flex-wrap gap-2">
          <AppButton
            size="sm"
            variant="outline"
            onClick={() => {
              setDetailPlanId(plan.id);
              setEditingPlan(null);
              setIsCreating(false);
              setActionError(null);
            }}
          >
            <Eye className="h-4 w-4" />
            Detalle
          </AppButton>
          <AppButton
            size="sm"
            variant="outline"
            onClick={() => {
              setEditingPlan(plan);
              setIsCreating(false);
              setActionError(null);
            }}
          >
            <Edit3 className="h-4 w-4" />
            Editar
          </AppButton>
          <AppButton
            size="sm"
            variant="outline"
            disabled={!plan.is_active || plan.code === "free"}
            title={plan.code === "free" ? "El plan free no se puede desactivar" : undefined}
            onClick={() => void handleDeactivate(plan)}
          >
            <Power className="h-4 w-4" />
            Desactivar
          </AppButton>
        </div>
      ),
    },
  ];

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Superadmin"
            title="Planes"
            description="Administra planes comerciales y accede a asignaciones por compañía."
            actions={
              <div className="flex flex-wrap gap-2">
                <AppButton asChild variant="outline">
                  <Link href="/dashboard/superadmin/companies">
                    <ExternalLink className="h-4 w-4" />
                    Asignaciones
                  </Link>
                </AppButton>
                <AppButton
                  onClick={() => {
                    setIsCreating(true);
                    setEditingPlan(null);
                    setDetailPlanId(null);
                    setActionError(null);
                  }}
                >
                  <Plus className="h-4 w-4" />
                  Crear plan
                </AppButton>
              </div>
            }
          />

          <AppCard>
            <AppCardHeader>
              <AppCardTitle>CRUD conectado</AppCardTitle>
              <AppCardDescription>
                El listado, detalle, creación, edición, desactivación y asignación
                usan endpoints admin reales. Los límites vacíos se envían como
                ilimitados.
              </AppCardDescription>
            </AppCardHeader>
          </AppCard>

          {successMessage ? (
            <div className="rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
              {successMessage}
            </div>
          ) : null}

          {actionError && !isPlanFormOpen ? (
            <ErrorState
              title="No se pudo completar la acción"
              description={actionError}
            />
          ) : null}

          {plansQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <RefreshCw className="h-5 w-5 animate-spin text-primary" />
                Cargando planes...
              </AppCardContent>
            </AppCard>
          ) : null}

          {plansQuery.isError ? (
            <ErrorState
              description={getApiErrorMessage(plansQuery.error)}
              onRetry={() => void plansQuery.refetch()}
            />
          ) : null}

          {!plansQuery.isLoading && !plansQuery.isError && !plans.length ? (
            <EmptyState
              title="No hay planes"
              description="Cuando el backend tenga planes configurados, aparecerán aquí."
            />
          ) : null}

          {!plansQuery.isLoading && !plansQuery.isError && plans.length ? (
            <DataTable columns={columns} data={plans} getRowKey={(plan) => plan.id} />
          ) : null}

          {isPlanFormOpen ? (
            <PlanModal
              title={editingPlan ? "Editar plan" : "Crear plan"}
              description={
                editingPlan
                  ? "Actualiza límites, features y datos comerciales del plan."
                  : "Define un nuevo plan comercial con límites y features."
              }
              onClose={() => {
                setIsCreating(false);
                setEditingPlan(null);
                setActionError(null);
              }}
            >
              <PlanForm
                plan={editingPlan}
                isSubmitting={createPlan.isPending || updatePlan.isPending}
                errorMessage={actionError}
                onCancel={() => {
                  setIsCreating(false);
                  setEditingPlan(null);
                  setActionError(null);
                }}
                onSubmit={handleSubmit}
              />
            </PlanModal>
          ) : null}

          {detailPlanId && !isPlanFormOpen ? (
            <PlanModal
              title="Detalle de plan"
              description="Consulta datos generales, límites y features configuradas."
              onClose={() => setDetailPlanId(null)}
            >
              {detailPlanQuery.isLoading ? (
                <div className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
                  <RefreshCw className="h-5 w-5 animate-spin text-primary" />
                  Cargando detalle...
                </div>
              ) : null}

              {detailPlanQuery.isError ? (
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                  <p className="font-medium text-destructive">No pudimos cargar el detalle</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {getApiErrorMessage(detailPlanQuery.error)}
                  </p>
                  <AppButton
                    className="mt-3"
                    variant="outline"
                    size="sm"
                    onClick={() => void detailPlanQuery.refetch()}
                  >
                    Reintentar
                  </AppButton>
                </div>
              ) : null}

              {detailPlan ? (
                <div className="grid gap-5 lg:grid-cols-[1fr_1.4fr]">
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-muted-foreground">Nombre</p>
                      <p className="font-medium text-foreground">{detailPlan.name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Código</p>
                      <p className="font-mono text-sm text-foreground">{detailPlan.code}</p>
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      {detailPlan.description || "Sin descripción."}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge tone={planTone(detailPlan)}>
                        {detailPlan.is_active ? "Activo" : "Inactivo"}
                      </StatusBadge>
                      <StatusBadge tone={publicTone(detailPlan)}>
                        {detailPlan.is_public ? "Público" : "Privado"}
                      </StatusBadge>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-lg border bg-background p-4">
                      <h3 className="text-sm font-semibold text-foreground">Límites</h3>
                      <dl className="mt-3 space-y-2 text-sm">
                        {detailLimitLabels.map((item) => (
                          <div key={item.key} className="flex justify-between gap-3">
                            <dt className="text-muted-foreground">{item.label}</dt>
                            <dd className="font-medium text-foreground">
                              {formatLimit(detailPlan.limits?.[item.key])}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                    <div className="rounded-lg border bg-background p-4">
                      <h3 className="text-sm font-semibold text-foreground">Features</h3>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {detailFeatureLabels.map((item) => (
                          <StatusBadge
                            key={item.key}
                            tone={detailPlan.features?.[item.key] ? "success" : "neutral"}
                          >
                            {item.label}
                          </StatusBadge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : null}
            </PlanModal>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
