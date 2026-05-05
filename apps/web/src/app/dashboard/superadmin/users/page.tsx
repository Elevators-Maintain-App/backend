"use client";

import { ArrowLeft, ChevronLeft, ChevronRight, Search } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppInput } from "@/components/forms/app-input";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useSuperAdminUsers } from "@/hooks/use-superadmin-users";
import type { SuperAdminUser, SuperAdminUserRole } from "@/types/superadmin";

const pageSize = 10;

const roleOptions: Array<{ value: SuperAdminUserRole; label: string }> = [
  { value: "technician", label: "Technician" },
  { value: "supervisor", label: "Supervisor" },
  { value: "admin", label: "Admin" },
  { value: "superAdmin", label: "Super Admin" },
  { value: "client", label: "Client" }
];

function roleBadgeTone(role: SuperAdminUserRole) {
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

function formatRole(role: SuperAdminUserRole) {
  return roleOptions.find((option) => option.value === role)?.label || role;
}

export default function SuperAdminUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<SuperAdminUserRole | "">("");
  const deferredSearch = useDeferredValue(search.trim());

  const usersQuery = useSuperAdminUsers({
    page,
    page_size: pageSize,
    search: deferredSearch || undefined,
    role: role || undefined
  });

  const usersPage = usersQuery.data;
  const hasUsers = Boolean(usersPage?.data.length);

  const columns = [
    {
      key: "user",
      header: "Usuario",
      cell: (user: SuperAdminUser) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">
            {user.display_name || "Sin nombre"}
          </p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </div>
      )
    },
    {
      key: "role",
      header: "Rol",
      cell: (user: SuperAdminUser) => (
        <StatusBadge tone={roleBadgeTone(user.role)}>
          {formatRole(user.role)}
        </StatusBadge>
      )
    },
    {
      key: "company",
      header: "Compania",
      cell: (user: SuperAdminUser) => (
        <span className="text-muted-foreground">
          {user.company_name || "Sin compania"}
        </span>
      )
    },
    {
      key: "status",
      header: "Estado",
      cell: (user: SuperAdminUser) => (
        <StatusBadge tone={user.is_active ? "success" : "danger"}>
          {user.is_active ? "Activo" : "Inactivo"}
        </StatusBadge>
      )
    },
    {
      key: "uid",
      header: "UID",
      cell: (user: SuperAdminUser) => (
        <span className="break-all font-mono text-xs text-muted-foreground">
          {user.uid}
        </span>
      )
    }
  ];

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Super Admin"
            title="Usuarios"
            description="Listado paginado y filtrado de usuarios registrados para VertiOne Web."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/superadmin">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          <AppCard>
            <AppCardHeader>
              <AppCardTitle>Filtros</AppCardTitle>
            </AppCardHeader>
            <AppCardContent className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
              <AppInput
                label="Buscar"
                placeholder="Email, nombre o documento"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <div className="space-y-2">
                <label
                  htmlFor="role-filter"
                  className="text-sm font-medium leading-none"
                >
                  Rol
                </label>
                <select
                  id="role-filter"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={role}
                  onChange={(event) => {
                    setRole(event.target.value as SuperAdminUserRole | "");
                    setPage(1);
                  }}
                >
                  <option value="">Todos</option>
                  {roleOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </AppCardContent>
          </AppCard>

          {usersQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <Search className="h-5 w-5 animate-pulse text-primary" />
                Cargando usuarios...
              </AppCardContent>
            </AppCard>
          ) : null}

          {usersQuery.isError ? (
            <ErrorState
              description="No fue posible cargar el listado de usuarios."
              onRetry={() => void usersQuery.refetch()}
            />
          ) : null}

          {!usersQuery.isLoading && !usersQuery.isError && !hasUsers ? (
            <EmptyState
              title="No encontramos usuarios"
              description="Ajusta la busqueda o el filtro de rol para intentar de nuevo."
            />
          ) : null}

          {!usersQuery.isLoading && !usersQuery.isError && hasUsers ? (
            <>
              <DataTable
                columns={columns}
                data={usersPage?.data || []}
                getRowKey={(user) => user.uid}
              />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Pagina {usersPage?.page || 1} de {usersPage?.total_pages || 1}
                  {" "}({usersPage?.total || 0} usuarios)
                </p>
                <div className="flex items-center gap-2">
                  <AppButton
                    variant="outline"
                    disabled={page <= 1}
                    onClick={() => setPage((currentPage) => Math.max(1, currentPage - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                  </AppButton>
                  <AppButton
                    variant="outline"
                    disabled={!usersPage || page >= usersPage.total_pages}
                    onClick={() => setPage((currentPage) => currentPage + 1)}
                  >
                    Siguiente
                    <ChevronRight className="h-4 w-4" />
                  </AppButton>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
