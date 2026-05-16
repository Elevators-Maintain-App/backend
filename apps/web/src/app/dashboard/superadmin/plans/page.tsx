"use client";

import { Edit3, ExternalLink, Plus, Power, RefreshCw, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { PlanForm, formatLimit } from "@/components/plans/plan-form";
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
  useCreateAdminPlan,
  useDeactivateAdminPlan,
  useDeleteAdminPlan,
  useUpdateAdminPlan,
} from "@/hooks/use-plans";
import type { Plan, PlanFormValues } from "@/types/plans";

function planTone(plan: Plan) {
  return plan.is_active ? "success" : "danger";
}

function publicTone(plan: Plan) {
  return plan.is_public ? "info" : "neutral";
}

function featuresSummary(plan: Plan) {
  const features = plan.features;
  if (!features) {
    return "Sin features";
  }

  return [
    features.offline_mode ? "Offline" : null,
    features.custom_checklists ? "Checklists" : null,
    features.advanced_dashboard ? "Dashboard" : null,
    features.evidence_editing ? "Evidencias" : null,
  ].filter(Boolean).join(", ") || "Sin features";
}

export default function SuperAdminPlansPage() {
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const plansQuery = useAdminPlans(true);
  const createPlan = useCreateAdminPlan();
  const updatePlan = useUpdateAdminPlan();
  const deactivatePlan = useDeactivateAdminPlan();
  const deletePlan = useDeleteAdminPlan();

  const plans = plansQuery.data || [];
  const showForm = isCreating || Boolean(editingPlan);

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

  const handleDelete = async (plan: Plan) => {
    const confirmed = window.confirm(
      `¿Eliminar el plan "${plan.name}"? Esta acción depende de soporte backend.`
    );
    if (!confirmed) {
      return;
    }

    setActionError(null);
    setSuccessMessage(null);
    try {
      await deletePlan.mutateAsync(plan.id);
      setSuccessMessage("Plan eliminado correctamente.");
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
              setEditingPlan(plan);
              setIsCreating(false);
              setActionError(null);
            }}
          >
            <Edit3 className="h-4 w-4" />
            Editar
          </AppButton>
          <AppButton size="sm" variant="outline" onClick={() => void handleDeactivate(plan)}>
            <Power className="h-4 w-4" />
            Desactivar
          </AppButton>
          <AppButton size="sm" variant="outline" onClick={() => void handleDelete(plan)}>
            <Trash2 className="h-4 w-4" />
            Eliminar
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
              <AppCardTitle>Soporte backend</AppCardTitle>
              <AppCardDescription>
                El listado y asignación de planes usan endpoints reales. Crear, editar,
                desactivar o eliminar quedan conectados a endpoints admin esperados y
                mostrarán el error del backend si todavía no existen.
              </AppCardDescription>
            </AppCardHeader>
          </AppCard>

          {successMessage ? (
            <div className="rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
              {successMessage}
            </div>
          ) : null}

          {actionError && !showForm ? (
            <ErrorState
              title="No se pudo completar la acción"
              description={actionError}
            />
          ) : null}

          {showForm ? (
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
        </div>
      </AppShell>
    </RoleGuard>
  );
}
