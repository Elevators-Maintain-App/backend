"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import { useCreateSuperadminUser } from "@/hooks/use-superadmin-users";
import { UserForm, type SuperadminUserFormValues } from "../_components/user-form";

export default function NewSuperAdminUserPage() {
  const router = useRouter();
  const createUserMutation = useCreateSuperadminUser();
  const [successMessage, setSuccessMessage] = useState("");

  async function onSubmit(values: SuperadminUserFormValues) {
    setSuccessMessage("");

    try {
      await createUserMutation.mutateAsync({
        display_name: values.display_name.trim(),
        email: values.email.trim(),
        phone: values.phone?.trim() || null,
        role: values.role,
        company_id: values.company_id,
        password: values.password?.trim() || null
      });

      setSuccessMessage("Usuario creado correctamente. Volviendo al listado...");
      window.setTimeout(() => {
        router.push("/dashboard/superadmin/users");
      }, 700);
    } catch {
      setSuccessMessage("");
    }
  }

  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Superadmin"
            title="Crear usuario"
            description="Alta de usuarios para la administracion global de VertiOne."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/superadmin/users">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          <UserForm
            mode="create"
            isSubmitting={createUserMutation.isPending}
            error={createUserMutation.error}
            successMessage={successMessage}
            onSubmit={onSubmit}
          />
        </div>
      </AppShell>
    </RoleGuard>
  );
}
