"use client";

import { FolderKanban } from "lucide-react";
import { SuperAdminPlaceholderPage } from "@/app/dashboard/superadmin/_components/superadmin-placeholder-page";

export default function SuperAdminProjectsPage() {
  return (
    <SuperAdminPlaceholderPage
      title="Proyectos"
      description="Administracion global de proyectos por compañia."
      message="Modulo de proyectos en preparacion."
      icon={FolderKanban}
    />
  );
}
