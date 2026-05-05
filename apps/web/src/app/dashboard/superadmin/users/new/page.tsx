"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { ArrowLeft, CheckCircle2, Loader2, Save } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { RoleGuard } from "@/components/auth/role-guard";
import { ErrorState, StatusBadge } from "@/components/feedback";
import { AppInput, AppSelect } from "@/components/forms";
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
import {
  useCreateSuperAdminUser,
  useSuperAdminCompanies,
  useSuperAdminCompanyClients,
  useSuperAdminDocumentTypes,
  useSuperAdminTechnicalLevels
} from "@/hooks/use-superadmin-users";
import type {
  CreateSuperAdminUserInput,
  SuperAdminCatalogItem,
  SuperAdminUserRole
} from "@/types/superadmin";

const roleOptions: Array<{ value: SuperAdminUserRole; label: string }> = [
  { value: "admin", label: "Admin" },
  { value: "supervisor", label: "Supervisor" },
  { value: "technician", label: "Technician" },
  { value: "client", label: "Client" },
  { value: "superAdmin", label: "Super Admin" }
];

const createUserSchema = z
  .object({
    display_name: z.string().trim().min(1, "El nombre es requerido"),
    email: z.string().trim().email("Ingresa un email valido"),
    phone_number: z.string().trim().min(1, "El telefono es requerido"),
    document_id: z.string().trim().min(1, "El documento es requerido"),
    document_type_id: z.coerce
      .number({ invalid_type_error: "El tipo de documento es requerido" })
      .int("El tipo de documento es requerido")
      .positive("El tipo de documento es requerido"),
    rol: z.enum(["technician", "supervisor", "admin", "superAdmin", "client"], {
      required_error: "El rol es requerido"
    }),
    company_id: z.string().trim().min(1, "La compania es requerida"),
    client_id: z.string().optional(),
    nivel: z.string().optional(),
    is_active: z.boolean().default(true)
  })
  .superRefine((value, ctx) => {
    if (value.rol === "client" && !value.client_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["client_id"],
        message: "El cliente es requerido para usuarios client"
      });
    }
  });

type CreateUserFormValues = z.infer<typeof createUserSchema>;

function toSelectOptions(items?: SuperAdminCatalogItem[]) {
  return (items || []).map((item) => ({
    value: item.id,
    label: item.name
  }));
}

function getApiErrorMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return "No fue posible crear el usuario. Revisa los datos e intenta nuevamente.";
}

export default function NewSuperAdminUserPage() {
  const router = useRouter();
  const [successMessage, setSuccessMessage] = useState("");
  const createUserMutation = useCreateSuperAdminUser();
  const companiesQuery = useSuperAdminCompanies();
  const documentTypesQuery = useSuperAdminDocumentTypes();

  const form = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      display_name: "",
      email: "",
      phone_number: "",
      document_id: "",
      document_type_id: 0,
      rol: "admin",
      company_id: "",
      client_id: "",
      nivel: "",
      is_active: true
    }
  });

  const selectedRole = form.watch("rol");
  const selectedCompanyId = form.watch("company_id");
  const clientsQuery = useSuperAdminCompanyClients(
    selectedRole === "client" ? selectedCompanyId : undefined
  );
  const technicalLevelsQuery = useSuperAdminTechnicalLevels(
    selectedRole === "technician" ? selectedCompanyId : undefined
  );

  useEffect(() => {
    form.setValue("client_id", "");
    form.setValue("nivel", "");
  }, [form, selectedCompanyId]);

  useEffect(() => {
    if (selectedRole !== "client") {
      form.setValue("client_id", "");
    }
    if (selectedRole !== "technician") {
      form.setValue("nivel", "");
    }
  }, [form, selectedRole]);

  const companyOptions = useMemo(
    () => toSelectOptions(companiesQuery.data),
    [companiesQuery.data]
  );
  const documentTypeOptions = useMemo(
    () => toSelectOptions(documentTypesQuery.data),
    [documentTypesQuery.data]
  );
  const clientOptions = useMemo(
    () => toSelectOptions(clientsQuery.data),
    [clientsQuery.data]
  );
  const technicalLevelOptions = useMemo(
    () => toSelectOptions(technicalLevelsQuery.data),
    [technicalLevelsQuery.data]
  );

  const isCatalogError = companiesQuery.isError || documentTypesQuery.isError;

  async function onSubmit(values: CreateUserFormValues) {
    const payload: CreateSuperAdminUserInput = {
      company_id: values.company_id,
      display_name: values.display_name.trim(),
      document_id: values.document_id.trim(),
      document_type_id: values.document_type_id,
      email: values.email.trim(),
      phone_number: values.phone_number.trim(),
      rol: values.rol,
      is_active: values.is_active
    };

    if (values.rol === "client") {
      payload.client_id = values.client_id;
    }

    if (values.rol === "technician" && values.nivel) {
      payload.nivel = values.nivel;
    }

    try {
      await createUserMutation.mutateAsync(payload);
      setSuccessMessage("Usuario creado correctamente. Volviendo al listado...");
      window.setTimeout(() => {
        router.push("/dashboard/superadmin/users");
      }, 900);
    } catch {
      setSuccessMessage("");
    }
  }

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Super Admin"
            title="Crear usuario"
            description="Alta protegida para usuarios operativos de VertiOne Web."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/superadmin/users">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          {isCatalogError ? (
            <ErrorState
              description="No fue posible cargar los catalogos necesarios para crear usuarios."
              onRetry={() => {
                void companiesQuery.refetch();
                void documentTypesQuery.refetch();
              }}
            />
          ) : null}

          <form onSubmit={form.handleSubmit(onSubmit)}>
            <AppCard>
              <AppCardHeader>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <AppCardTitle>Datos del usuario</AppCardTitle>
                    <AppCardDescription>
                      Los campos de cliente solo se habilitan para rol client.
                    </AppCardDescription>
                  </div>
                  <StatusBadge tone={selectedRole === "client" ? "info" : "neutral"}>
                    {roleOptions.find((option) => option.value === selectedRole)?.label}
                  </StatusBadge>
                </div>
              </AppCardHeader>

              <AppCardContent className="grid gap-5">
                {successMessage ? (
                  <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                    <CheckCircle2 className="h-4 w-4" />
                    {successMessage}
                  </div>
                ) : null}

                {createUserMutation.isError ? (
                  <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {getApiErrorMessage(createUserMutation.error)}
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
                    label="Email"
                    type="email"
                    placeholder="usuario@empresa.com"
                    error={form.formState.errors.email?.message}
                    {...form.register("email")}
                  />
                  <AppInput
                    label="Telefono"
                    placeholder="+507..."
                    error={form.formState.errors.phone_number?.message}
                    {...form.register("phone_number")}
                  />
                  <AppSelect
                    label="Rol"
                    options={roleOptions}
                    error={form.formState.errors.rol?.message}
                    {...form.register("rol")}
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
                    label="Tipo de documento"
                    options={documentTypeOptions}
                    placeholder={
                      documentTypesQuery.isLoading
                        ? "Cargando tipos..."
                        : "Seleccionar tipo"
                    }
                    disabled={documentTypesQuery.isLoading}
                    error={form.formState.errors.document_type_id?.message}
                    {...form.register("document_type_id")}
                  />
                  <AppInput
                    label="Documento"
                    placeholder="Documento"
                    error={form.formState.errors.document_id?.message}
                    {...form.register("document_id")}
                  />
                  {selectedRole === "technician" ? (
                    <AppSelect
                      label="Nivel tecnico"
                      options={technicalLevelOptions}
                      placeholder={
                        selectedCompanyId
                          ? "Seleccionar nivel"
                          : "Selecciona una compania primero"
                      }
                      disabled={!selectedCompanyId || technicalLevelsQuery.isLoading}
                      hint="Opcional segun la configuracion actual del backend."
                      error={form.formState.errors.nivel?.message}
                      {...form.register("nivel")}
                    />
                  ) : null}
                  {selectedRole === "client" ? (
                    <AppSelect
                      label="Cliente"
                      options={clientOptions}
                      placeholder={
                        selectedCompanyId
                          ? "Seleccionar cliente"
                          : "Selecciona una compania primero"
                      }
                      disabled={!selectedCompanyId || clientsQuery.isLoading}
                      hint={
                        clientsQuery.isError
                          ? "No fue posible cargar clientes para esta compania."
                          : "Solo se muestran clientes de la compania seleccionada."
                      }
                      error={form.formState.errors.client_id?.message}
                      {...form.register("client_id")}
                    />
                  ) : null}
                </div>

                <div className="flex flex-col-reverse gap-3 border-t pt-5 sm:flex-row sm:justify-end">
                  <AppButton asChild variant="outline">
                    <Link href="/dashboard/superadmin/users">Cancelar</Link>
                  </AppButton>
                  <AppButton
                    type="submit"
                    disabled={
                      createUserMutation.isPending ||
                      companiesQuery.isLoading ||
                      documentTypesQuery.isLoading
                    }
                  >
                    {createUserMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    Crear usuario
                  </AppButton>
                </div>
              </AppCardContent>
            </AppCard>
          </form>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
