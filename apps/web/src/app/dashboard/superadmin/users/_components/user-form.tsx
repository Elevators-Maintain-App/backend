"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { Loader2, Save } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppInput, AppSelect } from "@/components/forms";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useSuperAdminCompanies } from "@/hooks/use-superadmin-users";
import type {
  SuperadminUserDetail,
  SuperadminUserRole
} from "@/types/superadmin-users";

const roleOptions: Array<{ value: SuperadminUserRole; label: string }> = [
  { value: "admin", label: "Admin" },
  { value: "supervisor", label: "Supervisor" },
  { value: "technician", label: "Technician" },
  { value: "client", label: "Client" },
  { value: "superAdmin", label: "Super Admin" }
];

const statusOptions = [
  { value: "active", label: "Activo" },
  { value: "inactive", label: "Inactivo" }
];

const userFormSchema = z
  .object({
    display_name: z.string().trim().min(1, "El nombre es requerido"),
    email: z.string().trim().email("Ingresa un email valido"),
    phone: z.string().trim().optional(),
    role: z.enum(["technician", "supervisor", "admin", "superAdmin", "client"], {
      required_error: "El rol es requerido"
    }),
    company_id: z.string().trim().min(1, "La compania es requerida"),
    status: z.enum(["active", "inactive"]).default("active"),
    password: z.string().optional()
  })
  .superRefine((value, ctx) => {
    if (value.password && value.password.length < 6) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["password"],
        message: "La contrasena debe tener al menos 6 caracteres"
      });
    }
  });

export type SuperadminUserFormValues = z.infer<typeof userFormSchema>;

type UserFormProps = {
  mode: "create" | "edit";
  user?: SuperadminUserDetail;
  isSubmitting?: boolean;
  error?: unknown;
  successMessage?: string;
  submitLabel?: string;
  onSubmit: (values: SuperadminUserFormValues) => void | Promise<void>;
};

function getApiErrorMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }

  return "No fue posible guardar el usuario. Revisa los datos e intenta nuevamente.";
}

function getDefaultValues(
  mode: UserFormProps["mode"],
  user?: SuperadminUserDetail
): SuperadminUserFormValues {
  return {
    display_name: user?.display_name || "",
    email: user?.email || "",
    phone: user?.phone || user?.phone_number || "",
    role: user?.role || "admin",
    company_id: user?.company_id || "",
    status: user?.status === "inactive" ? "inactive" : "active",
    password: mode === "create" ? "" : undefined
  };
}

export function UserForm({
  mode,
  user,
  isSubmitting = false,
  error,
  successMessage,
  submitLabel,
  onSubmit
}: UserFormProps) {
  const companiesQuery = useSuperAdminCompanies();
  const form = useForm<SuperadminUserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: getDefaultValues(mode, user)
  });

  useEffect(() => {
    form.reset(getDefaultValues(mode, user));
  }, [form, mode, user]);

  const companyOptions = useMemo(
    () =>
      (companiesQuery.data || []).map((company) => ({
        value: company.id,
        label: company.name
      })),
    [companiesQuery.data]
  );

  const apiErrorMessage = error ? getApiErrorMessage(error) : "";
  const isEmailLocked = mode === "edit";

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <AppCard>
        <AppCardHeader>
          <AppCardTitle>
            {mode === "create" ? "Datos del nuevo usuario" : "Editar usuario"}
          </AppCardTitle>
          <AppCardDescription>
            {mode === "create"
              ? "Crea usuarios desde la capa web sin usar contratos legacy."
              : "Actualiza datos operativos. El correo se mantiene bloqueado por seguridad."}
          </AppCardDescription>
        </AppCardHeader>
        <AppCardContent className="grid gap-5">
          {successMessage ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {successMessage}
            </div>
          ) : null}

          {apiErrorMessage ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {apiErrorMessage}
            </div>
          ) : null}

          {companiesQuery.isError ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              No fue posible cargar el catalogo de companias. Puedes reintentar o
              volver al listado.
            </div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <AppInput
              label="Nombre"
              placeholder="Nombre completo"
              error={form.formState.errors.display_name?.message}
              {...form.register("display_name")}
            />
            <AppInput
              label="Correo"
              type="email"
              placeholder="usuario@empresa.com"
              disabled={isEmailLocked}
              hint={isEmailLocked ? "El endpoint web no cambia correos en edicion." : undefined}
              error={form.formState.errors.email?.message}
              {...form.register("email")}
            />
            <AppInput
              label="Telefono"
              placeholder="+507..."
              error={form.formState.errors.phone?.message}
              {...form.register("phone")}
            />
            <AppSelect
              label="Rol"
              options={roleOptions}
              error={form.formState.errors.role?.message}
              {...form.register("role")}
            />
            <AppSelect
              label="Compania"
              options={companyOptions}
              placeholder={
                companiesQuery.isLoading ? "Cargando companias..." : "Seleccionar compania"
              }
              disabled={companiesQuery.isLoading}
              error={form.formState.errors.company_id?.message}
              {...form.register("company_id")}
            />
            <AppSelect
              label="Estado"
              options={statusOptions}
              disabled={mode === "create"}
              hint={mode === "create" ? "Los usuarios nuevos se crean activos." : undefined}
              error={form.formState.errors.status?.message}
              {...form.register("status")}
            />
            {mode === "create" ? (
              <AppInput
                label="Contrasena"
                type="password"
                placeholder="Opcional"
                hint="Si se informa, debe tener al menos 6 caracteres."
                error={form.formState.errors.password?.message}
                {...form.register("password")}
              />
            ) : null}
          </div>

          <div className="flex flex-col-reverse gap-3 border-t pt-5 sm:flex-row sm:justify-end">
            <AppButton asChild variant="outline">
              <Link href="/dashboard/superadmin/users">Cancelar</Link>
            </AppButton>
            <AppButton
              type="submit"
              disabled={isSubmitting || companiesQuery.isLoading}
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {submitLabel || (mode === "create" ? "Crear usuario" : "Guardar cambios")}
            </AppButton>
          </div>
        </AppCardContent>
      </AppCard>
    </form>
  );
}
