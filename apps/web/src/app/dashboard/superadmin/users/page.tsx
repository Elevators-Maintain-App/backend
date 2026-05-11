"use client";

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Plus,
  Search,
} from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppInput, AppSelect } from "@/components/forms";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import { useSuperadminUsers } from "@/hooks/use-superadmin-users";
import type {
  SuperadminUserListItem,
  SuperadminUserRole,
  SuperadminUserStatus,
} from "@/types/superadmin-users";

const pageSize = 10;

const roleOptions: Array<{ value: SuperadminUserRole; label: string }> = [
  { value: "technician", label: "Technician" },
  { value: "supervisor", label: "Supervisor" },
  { value: "admin", label: "Admin" },
  { value: "superAdmin", label: "Super Admin" },
  { value: "client", label: "Client" },
];

const statusOptions: Array<{ value: SuperadminUserStatus; label: string }> = [
  { value: "active", label: "Activo" },
  { value: "inactive", label: "Inactivo" },
  { value: "unknown", label: "Desconocido" },
];

function roleBadgeTone(role: SuperadminUserRole) {
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

function statusBadgeTone(status: SuperadminUserStatus) {
  if (status === "active") {
    return "success";
  }
  if (status === "inactive") {
    return "danger";
  }
  return "neutral";
}

function formatRole(role: SuperadminUserRole) {
  return roleOptions.find((option) => option.value === role)?.label || role;
}

function formatStatus(status: SuperadminUserStatus) {
  return statusOptions.find((option) => option.value === status)?.label || status;
}

function formatDate(value?: string | null) {
  if (!value) {
    return "Sin fecha";
  }

  return new Intl.DateTimeFormat("es", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export default function SuperAdminUsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<SuperadminUserRole | "">("");
  const [status, setStatus] = useState<SuperadminUserStatus | "">("");
  const deferredSearch = useDeferredValue(search.trim());

  const usersQuery = useSuperadminUsers({
    page,
    page_size: pageSize,
    search: deferredSearch || undefined,
    role: role || undefined,
    status: status || undefined,
  });

  const usersPage = usersQuery.data;
  const users = usersPage?.items || [];
  const hasUsers = Boolean(users.length);

  const columns = [
    {
      key: "user",
      header: "Nombre",
      cell: (user: SuperadminUserListItem) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">
            {user.display_name || "Sin nombre"}
          </p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </div>
      ),
    },
    {
      key: "role",
      header: "Rol",
      cell: (user: SuperadminUserListItem) => (
        <StatusBadge tone={roleBadgeTone(user.role)}>
          {formatRole(user.role)}
        </StatusBadge>
      ),
    },
    {
      key: "company",
      header: "Compañía",
      cell: (user: SuperadminUserListItem) => (
        <span className="text-muted-foreground">
          {user.company_name || "Sin compañía"}
        </span>
      ),
    },
    {
      key: "status",
      header: "Estado",
      cell: (user: SuperadminUserListItem) => (
        <StatusBadge tone={statusBadgeTone(user.status)}>
          {formatStatus(user.status)}
        </StatusBadge>
      ),
    },
    {
      key: "created_at",
      header: "Fecha creación",
      cell: (user: SuperadminUserListItem) => (
        <span className="text-muted-foreground">
          {formatDate(user.created_at)}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Acción",
      cell: (user: SuperadminUserListItem) => (
        <AppButton asChild variant="outline" size="sm">
          <Link href={`/dashboard/superadmin/users/${user.uid}`}>
            <Eye className="h-4 w-4" />
            Ver detalle
          </Link>
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
            title="Usuarios"
            description="Gestiona los usuarios registrados en la plataforma."
            actions={
              <AppButton asChild>
                <Link href="/dashboard/superadmin/users/new">
                  <Plus className="h-4 w-4" />
                  Crear usuario
                </Link>
              </AppButton>
            }
          />

          <AppCard>
            <AppCardHeader>
              <AppCardTitle>Filtros</AppCardTitle>
            </AppCardHeader>
            <AppCardContent className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px_220px]">
              <AppInput
                label="Buscar"
                placeholder="Nombre o correo"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <AppSelect
                label="Rol"
                value={role}
                onChange={(event) => {
                  setRole(event.target.value as SuperadminUserRole | "");
                  setPage(1);
                }}
                placeholder="Todos"
                options={roleOptions}
              />
              <AppSelect
                label="Estado"
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value as SuperadminUserStatus | "");
                  setPage(1);
                }}
                placeholder="Todos"
                options={statusOptions}
              />
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
              description="Ajusta la búsqueda o los filtros para intentar de nuevo."
            />
          ) : null}

          {!usersQuery.isLoading && !usersQuery.isError && hasUsers ? (
            <>
              <DataTable
                columns={columns}
                data={users}
                getRowKey={(user) => user.uid}
              />

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Página {usersPage?.page || 1} de {usersPage?.total_pages || 1}{" "}
                  ({usersPage?.total || 0} usuarios)
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
