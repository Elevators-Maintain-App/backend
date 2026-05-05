"use client";

import { ClipboardList, FolderKanban, Package, Wrench } from "lucide-react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useClientDashboard } from "@/hooks/use-client-dashboard";
import type { ClientRecentOrder } from "@/types/client-dashboard";

const missingClientIdMessage =
  "Tu usuario aún no está asociado a un cliente. Contacta al administrador.";

function getClientDashboardErrorMessage(error: unknown) {
  const message = error instanceof Error ? error.message : "";
  if (message === "El usuario cliente no tiene client_id asociado") {
    return missingClientIdMessage;
  }
  return message || "No fue posible cargar el dashboard de cliente.";
}

function MetricCard({
  title,
  value,
  icon: Icon,
  tone = "info",
  href
}: {
  title: string;
  value: number;
  icon: typeof FolderKanban;
  tone?: "info" | "success" | "warning" | "neutral";
  href?: string;
}) {
  const content = (
    <AppCard>
      <AppCardHeader>
        <div className="flex items-center justify-between gap-3">
          <AppCardTitle>{title}</AppCardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </AppCardHeader>
      <AppCardContent>
        <p className="text-3xl font-semibold tracking-normal">{value}</p>
        <StatusBadge className="mt-3" tone={tone}>
          Visible para cliente
        </StatusBadge>
      </AppCardContent>
    </AppCard>
  );

  if (!href) {
    return content;
  }

  return (
    <Link href={href} className="block">
      {content}
    </Link>
  );
}

function RecentOrderItem({ order }: { order: ClientRecentOrder }) {
  return (
    <div className="grid gap-3 border-b py-4 last:border-b-0 md:grid-cols-[minmax(0,1fr)_160px_140px] md:items-center">
      <div className="min-w-0">
        <p className="font-medium text-foreground">
          {order.reference || "Sin referencia"}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          {order.project} / {order.unit}
        </p>
      </div>
      <StatusBadge tone={order.status === "Cerrada" ? "success" : "warning"}>
        {order.status}
      </StatusBadge>
      <p className="text-sm text-muted-foreground">
        {order.date || "Sin fecha"}
      </p>
    </div>
  );
}

export default function ClientDashboardPage() {
  const dashboardQuery = useClientDashboard();
  const dashboard = dashboardQuery.data;

  return (
    <RoleGuard allowedRoles={["client"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Cliente"
            title={dashboard?.client.name || "Dashboard de cliente"}
            description="Resumen inicial de proyectos, unidades y ordenes visibles para tu cliente asociado."
          />

          {dashboardQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <ClipboardList className="h-5 w-5 animate-pulse text-primary" />
                Cargando dashboard...
              </AppCardContent>
            </AppCard>
          ) : null}

          {dashboardQuery.isError ? (
            <ErrorState
              description={getClientDashboardErrorMessage(dashboardQuery.error)}
              onRetry={() => void dashboardQuery.refetch()}
            />
          ) : null}

          {dashboard && !dashboardQuery.isError ? (
            <>
              <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  title="Proyectos"
                  value={dashboard.summary.total_projects}
                  icon={FolderKanban}
                  tone="info"
                />
                <MetricCard
                  title="Unidades"
                  value={dashboard.summary.total_units}
                  icon={Package}
                  tone="neutral"
                  href="/dashboard/client/units"
                />
                <MetricCard
                  title="Ordenes abiertas"
                  value={dashboard.summary.open_orders}
                  icon={Wrench}
                  tone="warning"
                  href="/dashboard/client/orders"
                />
                <MetricCard
                  title="Ordenes cerradas"
                  value={dashboard.summary.closed_orders}
                  icon={ClipboardList}
                  tone="success"
                  href="/dashboard/client/orders?status=Cerrada"
                />
              </section>

              <AppCard>
                <AppCardHeader>
                  <AppCardTitle>Ultimas ordenes</AppCardTitle>
                  <AppCardDescription>
                    Las ultimas 5 ordenes visibles para tu cliente.
                  </AppCardDescription>
                </AppCardHeader>
                <AppCardContent>
                  {dashboard.recent_orders.length ? (
                    dashboard.recent_orders.map((order) => (
                      <RecentOrderItem key={order.id} order={order} />
                    ))
                  ) : (
                    <EmptyState
                      title="No hay ordenes recientes"
                      description="Cuando existan ordenes asociadas a tu cliente, apareceran aqui."
                    />
                  )}
                </AppCardContent>
              </AppCard>
            </>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
