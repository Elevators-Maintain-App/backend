"use client";

import { Building2, RefreshCw, Repeat2 } from "lucide-react";
import { useMemo, useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AssignPlanDialog } from "@/components/plans/assign-plan-dialog";
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
  useAssignCompanyPlan,
  useCompanySubscriptionStatuses,
  useSuperAdminCompaniesForPlans,
} from "@/hooks/use-plans";
import type { AssignPlanPayload, CompanySubscriptionStatus, SuperAdminCompany } from "@/types/plans";

function subscriptionTone(status?: string | null) {
  if (status === "active" || status === "trialing" || status === "trial") {
    return "success";
  }
  if (status === "past_due" || status === "suspended") {
    return "warning";
  }
  if (status === "cancelled" || status === "expired") {
    return "danger";
  }
  return "neutral";
}

function formatStatus(status?: string | null) {
  if (!status) {
    return "Sin suscripción";
  }

  const labels: Record<string, string> = {
    active: "Activa",
    trialing: "Trial",
    trial: "Trial",
    past_due: "Pago pendiente",
    suspended: "Suspendida",
    cancelled: "Cancelada",
    expired: "Expirada",
  };

  return labels[status] || status;
}

export default function SuperAdminCompaniesPage() {
  const [selectedCompany, setSelectedCompany] = useState<SuperAdminCompany | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const companiesQuery = useSuperAdminCompaniesForPlans();
  const plansQuery = useAdminPlans(true);
  const companies = useMemo(() => companiesQuery.data || [], [companiesQuery.data]);
  const statusQueries = useCompanySubscriptionStatuses(companies);
  const assignPlan = useAssignCompanyPlan();

  const statusByCompanyId = useMemo(() => {
    return new Map(
      companies.map((company, index) => [
        company.id,
        statusQueries[index]?.data as CompanySubscriptionStatus | undefined,
      ])
    );
  }, [companies, statusQueries]);

  const selectedStatus = selectedCompany
    ? statusByCompanyId.get(selectedCompany.id) || null
    : null;

  const handleAssign = async (payload: AssignPlanPayload) => {
    if (!selectedCompany) {
      return;
    }

    setActionError(null);
    setSuccessMessage(null);

    try {
      await assignPlan.mutateAsync({
        companyId: selectedCompany.id,
        payload,
      });
      setSuccessMessage(`Plan actualizado para ${selectedCompany.name}.`);
      setSelectedCompany(null);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    }
  };

  const columns = [
    {
      key: "company",
      header: "Compañía",
      cell: (company: SuperAdminCompany) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{company.name}</p>
          <p className="truncate text-xs text-muted-foreground">
            {company.email || company.documento || company.id}
          </p>
        </div>
      ),
    },
    {
      key: "plan",
      header: "Plan actual",
      cell: (company: SuperAdminCompany) => {
        const status = statusByCompanyId.get(company.id);
        const queryIndex = companies.findIndex((item) => item.id === company.id);
        const query = statusQueries[queryIndex];

        if (query?.isLoading) {
          return <span className="text-sm text-muted-foreground">Cargando...</span>;
        }

        if (query?.isError) {
          return (
            <span className="text-sm text-destructive">
              {getApiErrorMessage(query.error)}
            </span>
          );
        }

        return (
          <div className="space-y-1">
            <p className="font-medium text-foreground">{status?.plan?.name || "Sin plan"}</p>
            <p className="text-xs text-muted-foreground">{status?.plan?.code || "N/A"}</p>
          </div>
        );
      },
    },
    {
      key: "subscription",
      header: "Suscripción",
      cell: (company: SuperAdminCompany) => {
        const status = statusByCompanyId.get(company.id);
        return (
          <StatusBadge tone={subscriptionTone(status?.subscription?.status)}>
            {formatStatus(status?.subscription?.status)}
          </StatusBadge>
        );
      },
    },
    {
      key: "usage",
      header: "Uso mensual",
      cell: (company: SuperAdminCompany) => {
        const status = statusByCompanyId.get(company.id);
        if (!status?.usage) {
          return <span className="text-sm text-muted-foreground">Sin datos</span>;
        }

        return (
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Órdenes: {status.usage.work_orders_created}</p>
            <p>PDFs: {status.usage.pdf_reports_generated}</p>
            <p>Usuarios: {status.usage.users_count}</p>
          </div>
        );
      },
    },
    {
      key: "actions",
      header: "Acción",
      cell: (company: SuperAdminCompany) => (
        <AppButton
          size="sm"
          variant="outline"
          onClick={() => {
            setSelectedCompany(company);
            setActionError(null);
          }}
        >
          <Repeat2 className="h-4 w-4" />
          Cambiar plan
        </AppButton>
      ),
    },
  ];

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Superadmin"
            title="Compañías y suscripciones"
            description="Consulta el plan actual de cada compañía y cambia asignaciones manualmente."
          />

          <AppCard>
            <AppCardHeader>
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <AppCardTitle>Listado mínimo de compañías</AppCardTitle>
                  <AppCardDescription className="mt-1">
                    Se usa el catálogo web disponible de compañías. Si el backend
                    expone más campos adelante, esta tabla puede mostrar email,
                    documento y métricas adicionales.
                  </AppCardDescription>
                </div>
              </div>
            </AppCardHeader>
          </AppCard>

          {successMessage ? (
            <div className="rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
              {successMessage}
            </div>
          ) : null}

          {companiesQuery.isLoading || plansQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <RefreshCw className="h-5 w-5 animate-spin text-primary" />
                Cargando compañías y planes...
              </AppCardContent>
            </AppCard>
          ) : null}

          {companiesQuery.isError ? (
            <ErrorState
              description={getApiErrorMessage(companiesQuery.error)}
              onRetry={() => void companiesQuery.refetch()}
            />
          ) : null}

          {plansQuery.isError ? (
            <ErrorState
              title="No pudimos cargar los planes"
              description={getApiErrorMessage(plansQuery.error)}
              onRetry={() => void plansQuery.refetch()}
            />
          ) : null}

          {!companiesQuery.isLoading && !companiesQuery.isError && !companies.length ? (
            <EmptyState
              title="No hay compañías disponibles"
              description="El endpoint de catálogo no devolvió compañías para gestionar."
            />
          ) : null}

          {!companiesQuery.isLoading && !companiesQuery.isError && companies.length ? (
            <DataTable columns={columns} data={companies} getRowKey={(company) => company.id} />
          ) : null}

          {selectedCompany ? (
            <AssignPlanDialog
              company={selectedCompany}
              plans={plansQuery.data || []}
              currentStatus={selectedStatus}
              errorMessage={actionError}
              isSubmitting={assignPlan.isPending}
              onClose={() => {
                setSelectedCompany(null);
                setActionError(null);
              }}
              onSubmit={handleAssign}
            />
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
