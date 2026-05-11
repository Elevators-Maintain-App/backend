"use client";

import { CreditCard } from "lucide-react";
import { SuperAdminPlaceholderPage } from "@/app/dashboard/superadmin/_components/superadmin-placeholder-page";

export default function SuperAdminPlansPage() {
  return (
    <SuperAdminPlaceholderPage
      title="Planes"
      description="Gestion futura de planes y capacidades comerciales."
      message="Módulo de planes en preparación."
      icon={CreditCard}
    />
  );
}
