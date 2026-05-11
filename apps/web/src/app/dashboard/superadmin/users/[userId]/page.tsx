"use client";

import {
  ArrowLeft,
  Ban,
  Loader2,
  Pencil,
  Trash2,
  UserRound,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import {
  useDeleteSuperadminUser,
  useDisableSuperadminUser,
  useSuperadminUser,
  useUpdateSuperadminUser,
} from "@/hooks/use-superadmin-users";
import type {
  SuperadminUserRole,
  SuperadminUserStatus,
} from "@/types/superadmin-users";
import { UserForm, type SuperadminUserFormValues } from "../_components/user-form";

const roleLabels: Record<SuperadminUserRole, string> = {
  admin: "Admin",
  client: "Client",
  superAdmin: "Super Admin",
  supervisor: "Supervisor",
  technician: "Technician",
};

const statusLabels: Record<SuperadminUserStatus, string> = {
  active: "Activo",
  inactive: "Inactivo",
  unknown: "Desconocido",
};

function statusBadgeTone(status: SuperadminUserStatus) {
  if (status === "active") {
    return "success";
  }
  if (status === "inactive") {
    return "danger";
  }
  return "neutral";
}

function formatDate(value?: string | null) {
  if (!value) {
    return "Sin fecha";
  }

  return new Intl.DateTimeFormat("es", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value?: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <div className="break-words text-sm text-foreground">
        {value || "No disponible"}
      </div>
    </div>
  );
}

export default function SuperAdminUserDetailPage() {
  const params = useParams<{ userId: string }>();
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const userQuery = useSuperadminUser(params.userId);
  const updateUserMutation = useUpdateSuperadminUser();
  const disableUserMutation = useDisableSuperadminUser();
  const deleteUserMutation = useDeleteSuperadminUser();
  const user = userQuery.data;
  const isActionPending =
    updateUserMutation.isPending ||
    disableUserMutation.isPending ||
    deleteUserMutation.isPending;

  async function handleUpdate(values: SuperadminUserFormValues) {
    if (!user) {
      return;
    }

    setSuccessMessage("");
    setActionError("");

    try {
      await updateUserMutation.mutateAsync({
        uid: user.uid,
        payload: {
          display_name: values.display_name.trim(),
          phone: values.phone?.trim() || null,
          role: values.role,
          company_id: values.company_id,
          status: values.status
        }
      });
      setIsEditing(false);
      setSuccessMessage("Usuario actualizado correctamente.");
    } catch {
      setSuccessMessage("");
    }
  }

  async function handleDisable() {
    if (!user) {
      return;
    }

    const confirmed = window.confirm(
      `Vas a inhabilitar a ${user.display_name || user.email}. El usuario no deberia poder operar desde la plataforma. ¿Deseas continuar?`
    );

    if (!confirmed) {
      return;
    }

    setSuccessMessage("");
    setActionError("");

    try {
      await disableUserMutation.mutateAsync(user.uid);
      setSuccessMessage("Usuario inhabilitado correctamente.");
    } catch {
      setActionError("No fue posible inhabilitar el usuario.");
    }
  }

  async function handleDelete() {
    if (!user) {
      return;
    }

    const confirmed = window.confirm(
      `Esta accion eliminara a ${user.display_name || user.email}. No se puede deshacer desde la interfaz. ¿Confirmas la eliminacion?`
    );

    if (!confirmed) {
      return;
    }

    setSuccessMessage("");
    setActionError("");

    try {
      await deleteUserMutation.mutateAsync(user.uid);
      router.push("/dashboard/superadmin/users");
    } catch {
      setActionError("No fue posible eliminar el usuario.");
    }
  }

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Superadmin"
            title={user?.display_name || "Detalle de usuario"}
            description="Información operativa del usuario registrado en la plataforma."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/superadmin/users">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          {userQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                Cargando usuario...
              </AppCardContent>
            </AppCard>
          ) : null}

          {userQuery.isError ? (
            <ErrorState
              description="No fue posible cargar el detalle del usuario."
              onRetry={() => void userQuery.refetch()}
            />
          ) : null}

          {user ? (
            <section className="grid gap-6">
              {successMessage ? (
                <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                  {successMessage}
                </div>
              ) : null}

              {actionError ? (
                <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {actionError}
                </div>
              ) : null}

              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
                <AppCard>
                  <AppCardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex min-w-0 items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                          <UserRound className="h-5 w-5" />
                        </div>
                        <div className="min-w-0">
                          <AppCardTitle>{user.display_name || "Sin nombre"}</AppCardTitle>
                          <AppCardDescription className="mt-1">
                            {user.email}
                          </AppCardDescription>
                        </div>
                      </div>
                      <StatusBadge tone={statusBadgeTone(user.status)}>
                        {statusLabels[user.status]}
                      </StatusBadge>
                    </div>
                  </AppCardHeader>
                  <AppCardContent className="grid gap-5 md:grid-cols-2">
                    <DetailRow label="Nombre" value={user.display_name} />
                    <DetailRow label="Correo" value={user.email} />
                    <DetailRow label="Teléfono" value={user.phone || user.phone_number} />
                    <DetailRow label="Rol" value={roleLabels[user.role] || user.role} />
                    <DetailRow
                      label="Compañía"
                      value={user.company_name || user.company_id}
                    />
                    <DetailRow
                      label="Estado"
                      value={
                        <StatusBadge tone={statusBadgeTone(user.status)}>
                          {statusLabels[user.status]}
                        </StatusBadge>
                      }
                    />
                    <DetailRow label="Fecha creación" value={formatDate(user.created_at)} />
                    <DetailRow label="Fecha actualización" value={formatDate(user.updated_at)} />
                  </AppCardContent>
                </AppCard>

                <AppCard>
                  <AppCardHeader>
                    <AppCardTitle>Acciones</AppCardTitle>
                    <AppCardDescription>
                      Gestiona el ciclo de vida del usuario desde los endpoints web.
                    </AppCardDescription>
                  </AppCardHeader>
                  <AppCardContent className="space-y-2">
                    <AppButton
                      className="w-full justify-start"
                      variant={isEditing ? "secondary" : "outline"}
                      disabled={isActionPending}
                      onClick={() => setIsEditing((current) => !current)}
                    >
                      <Pencil className="h-4 w-4" />
                      {isEditing ? "Cerrar edicion" : "Editar"}
                    </AppButton>
                    <AppButton
                      className="w-full justify-start"
                      variant="outline"
                      disabled={isActionPending || user.status === "inactive"}
                      onClick={() => void handleDisable()}
                    >
                      {disableUserMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Ban className="h-4 w-4" />
                      )}
                      Inhabilitar
                    </AppButton>
                    <AppButton
                      className="w-full justify-start"
                      variant="destructive"
                      disabled={isActionPending}
                      onClick={() => void handleDelete()}
                    >
                      {deleteUserMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                      Eliminar
                    </AppButton>
                    <p className="pt-2 text-xs leading-5 text-muted-foreground">
                      Las acciones destructivas piden confirmacion antes de llamar al
                      backend.
                    </p>
                  </AppCardContent>
                </AppCard>
              </div>

              {isEditing ? (
                <UserForm
                  mode="edit"
                  user={user}
                  isSubmitting={updateUserMutation.isPending}
                  error={updateUserMutation.error}
                  onSubmit={handleUpdate}
                  submitLabel="Guardar cambios"
                />
              ) : null}
            </section>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
