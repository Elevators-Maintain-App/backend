"use client";

import {
  Activity,
  ArrowRight,
  Building2,
  CalendarDays,
  ClipboardList,
  CreditCard,
  FolderKanban,
  Users,
} from "lucide-react";
import Link from "next/link";
import { RoleGuard } from "@/components/auth/role-guard";
import { ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import {
  useSuperAdminCompanies,
  useSuperAdminUsers,
  useSuperAdminUsersSummary,
} from "@/hooks/use-superadmin-users";
import type { SuperAdminUser, SuperAdminUserRole } from "@/types/superadmin";

const planDistribution = [
  { label: "Free", value: 8, tone: "neutral" as const },
  { label: "Básico", value: 18, tone: "info" as const },
  { label: "Pro", value: 11, tone: "success" as const },
  { label: "Enterprise", value: 4, tone: "warning" as const },
];

const futureMetrics = [
  {
    label: "Órdenes por compañía",
    description: "Comparativo global por cuenta",
    icon: ClipboardList,
    progress: 68,
  },
  {
    label: "Usuarios nuevos por mes",
    description: "Tendencia de altas recientes",
    icon: CalendarDays,
    progress: 42,
  },
  {
    label: "Órdenes por mes",
    description: "Actividad operacional consolidada",
    icon: Activity,
    progress: 56,
  },
];

function formatRole(role: SuperAdminUserRole) {
  const labels: Record<SuperAdminUserRole, string> = {
    admin: "Admin",
    client: "Cliente",
    superAdmin: "Super Admin",
    supervisor: "Supervisor",
    technician: "Técnico",
  };

  return labels[role] || role;
}

function roleTone(role: SuperAdminUserRole) {
  if (role === "superAdmin") {
    return "info";
  }
  if (role === "admin" || role === "supervisor") {
    return "success";
  }
  if (role === "technician") {
    return "warning";
  }
  return "neutral";
}

function SummaryCard({
  title,
  value,
  description,
  href,
  icon: Icon,
}: {
  title: string;
  value: number | string;
  description: string;
  href: string;
  icon: typeof Building2;
}) {
  return (
    <Link href={href} className="block">
      <AppCard className="h-full transition-colors hover:border-primary/50 hover:bg-muted/30">
        <AppCardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </div>
        </AppCardHeader>
        <AppCardContent>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-semibold tracking-normal text-foreground">
            {value}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        </AppCardContent>
      </AppCard>
    </Link>
  );
}

function RecentUserRow({ user }: { user: SuperAdminUser }) {
  return (
    <div className="grid gap-3 border-b py-4 last:border-b-0 md:grid-cols-[minmax(0,1fr)_120px_minmax(120px,180px)_120px] md:items-center">
      <div className="min-w-0">
        <p className="truncate font-medium text-foreground">
          {user.display_name || "Sin nombre"}
        </p>
        <p className="mt-1 truncate text-xs text-muted-foreground">
          {user.email}
        </p>
      </div>
      <StatusBadge tone={roleTone(user.role)}>{formatRole(user.role)}</StatusBadge>
      <p className="truncate text-sm text-muted-foreground">
        {user.company_name || "Sin compañía"}
      </p>
      <p className="text-sm text-muted-foreground">Sin fecha</p>
    </div>
  );
}

export default function SuperAdminDashboardPage() {
  const summaryQuery = useSuperAdminUsersSummary();
  const companiesQuery = useSuperAdminCompanies();
  const recentUsersQuery = useSuperAdminUsers({
    page: 1,
    page_size: 5,
  });

  const companyCount = companiesQuery.data?.length;
  const recentUsers = recentUsersQuery.data?.data || [];

  // TODO: conectar con endpoint /api/web/superadmin/overview cuando exista
  // para reemplazar totales de proyectos, planes y metricas operativas futuras.
  const projectCount = "Próximamente";
  const plansValue = "Próximamente";

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Superadmin"
            title="Panel de control"
            description="Resumen operativo global de compañías, proyectos, usuarios y planes."
          />

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <SummaryCard
              title="Compañías"
              value={companiesQuery.isLoading ? "..." : companyCount ?? 0}
              description="Activas en plataforma"
              href="/dashboard/superadmin/companies"
              icon={Building2}
            />
            <SummaryCard
              title="Proyectos"
              value={projectCount}
              description="Consolidado global"
              href="/dashboard/superadmin/projects"
              icon={FolderKanban}
            />
            <SummaryCard
              title="Usuarios"
              value={
                summaryQuery.isLoading
                  ? "..."
                  : summaryQuery.data?.total_users ?? 0
              }
              description="Registrados"
              href="/dashboard/superadmin/users"
              icon={Users}
            />
            <SummaryCard
              title="Planes"
              value={plansValue}
              description="Módulo en preparación"
              href="/dashboard/superadmin/plans"
              icon={CreditCard}
            />
          </section>

          {summaryQuery.isError || companiesQuery.isError ? (
            <ErrorState
              description="No fue posible cargar todos los indicadores disponibles."
              onRetry={() => {
                void summaryQuery.refetch();
                void companiesQuery.refetch();
              }}
            />
          ) : null}

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.75fr)]">
            <AppCard>
              <AppCardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <AppCardTitle>Últimos usuarios creados</AppCardTitle>
                    <AppCardDescription className="mt-1">
                      Registros recientes disponibles desde el listado web.
                    </AppCardDescription>
                  </div>
                  <Link
                    href="/dashboard/superadmin/users"
                    className="text-sm font-medium text-primary hover:underline"
                  >
                    Ver todos
                  </Link>
                </div>
              </AppCardHeader>
              <AppCardContent>
                {recentUsersQuery.isError ? (
                  <div className="rounded-lg border border-border/70 bg-muted/30 px-4 py-5 text-sm text-muted-foreground">
                    No fue posible cargar usuarios recientes.
                  </div>
                ) : recentUsersQuery.isLoading ? (
                  <div className="py-6 text-sm text-muted-foreground">
                    Cargando usuarios recientes...
                  </div>
                ) : recentUsers.length ? (
                  recentUsers.map((user) => (
                    <RecentUserRow key={user.uid} user={user} />
                  ))
                ) : (
                  <div className="rounded-lg border border-dashed border-border px-4 py-8 text-center">
                    <p className="text-sm font-medium text-foreground">
                      No hay usuarios recientes
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Cuando existan usuarios registrados, aparecerán aquí.
                    </p>
                  </div>
                )}
              </AppCardContent>
            </AppCard>

            <AppCard>
              <AppCardHeader>
                <AppCardTitle>Usuarios por plan</AppCardTitle>
                <AppCardDescription className="mt-1">
                  Distribución temporal mientras se define el módulo de planes.
                </AppCardDescription>
              </AppCardHeader>
              <AppCardContent className="space-y-4">
                {planDistribution.map((plan) => {
                  const maxValue = Math.max(
                    ...planDistribution.map((item) => item.value)
                  );
                  const width = `${Math.max(12, (plan.value / maxValue) * 100)}%`;

                  return (
                    <div key={plan.label} className="space-y-2">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <StatusBadge tone={plan.tone}>{plan.label}</StatusBadge>
                        </div>
                        <span className="text-sm font-medium text-foreground">
                          {plan.value}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-primary/70"
                          style={{ width }}
                        />
                      </div>
                    </div>
                  );
                })}
                <p className="text-xs leading-5 text-muted-foreground">
                  TODO: conectar con endpoint /api/web/superadmin/plans cuando
                  exista el contrato.
                </p>
              </AppCardContent>
            </AppCard>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            {futureMetrics.map((metric) => {
              const Icon = metric.icon;

              return (
                <AppCard key={metric.label}>
                  <AppCardHeader>
                    <div className="flex items-start gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <AppCardTitle>{metric.label}</AppCardTitle>
                        <AppCardDescription className="mt-1">
                          {metric.description}
                        </AppCardDescription>
                      </div>
                    </div>
                  </AppCardHeader>
                  <AppCardContent>
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className="h-2 rounded-full bg-primary/60"
                        style={{ width: `${metric.progress}%` }}
                      />
                    </div>
                    <p className="mt-3 text-xs text-muted-foreground">
                      Métrica futura, pendiente de endpoint web.
                    </p>
                  </AppCardContent>
                </AppCard>
              );
            })}
          </section>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
