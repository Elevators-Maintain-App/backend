"use client";

import { Building2 } from "lucide-react";
import { SuperAdminPlaceholderPage } from "@/app/dashboard/superadmin/_components/superadmin-placeholder-page";

export default function SuperAdminCompaniesPage() {
  return (
    <SuperAdminPlaceholderPage
      title="Compañías"
      description="Administracion global de compañias registradas en VertiOne."
      message="Modulo de compañias en preparacion."
      icon={Building2}
    />
  );
}
