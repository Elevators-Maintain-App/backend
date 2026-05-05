"use client";

import { ArrowRight, Users } from "lucide-react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { ErrorState } from "@/components/feedback/error-state";
import { StatusBadge } from "@/components/feedback/status-badge";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useSuperAdminUsersSummary } from "@/hooks/use-superadmin-users";

export default function SuperAdminDashboardPage() {
  const summaryQuery = useSuperAdminUsersSummary();

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Super Admin"
            title="Dashboard de super admin"
            description="Vista operativa inicial para supervisar usuarios registrados en VertiOne."
          />

          {summaryQuery.isError ? (
            <ErrorState
              description="No fue posible cargar el resumen de usuarios."
              onRetry={() => void summaryQuery.refetch()}
            />
          ) : (
            <Link href="/dashboard/superadmin/users" className="block">
              <AppCard className="transition-colors hover:border-primary/50 hover:bg-muted/30">
                <AppCardHeader>
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                        <Users className="h-5 w-5" />
                      </div>
                      <div>
                        <AppCardTitle>Usuarios registrados</AppCardTitle>
                        <AppCardDescription>
                          Total de usuarios disponibles para la consola web.
                        </AppCardDescription>
                      </div>
                    </div>
                    <ArrowRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                </AppCardHeader>
                <AppCardContent className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-4xl font-semibold tracking-normal">
                      {summaryQuery.isLoading
                        ? "..."
                        : summaryQuery.data?.total_users ?? 0}
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Clic para ver listado, busqueda y filtros.
                    </p>
                  </div>
                  <StatusBadge tone="info">/api/web/superadmin</StatusBadge>
                </AppCardContent>
              </AppCard>
            </Link>
          )}

          <AppCard>
            <AppCardHeader>
              <AppCardTitle>Modulo en construccion</AppCardTitle>
              <AppCardDescription>
                Este dashboard ira sumando metricas reales por rol sin consumir
                endpoints legacy.
              </AppCardDescription>
            </AppCardHeader>
            <AppCardContent>
              <AppButton asChild variant="outline">
                <Link href="/dashboard/superadmin/users">Ver usuarios</Link>
              </AppButton>
            </AppCardContent>
          </AppCard>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
