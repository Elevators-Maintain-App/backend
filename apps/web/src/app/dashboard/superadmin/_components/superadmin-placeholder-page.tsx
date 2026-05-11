"use client";

import type { LucideIcon } from "lucide-react";
import { RoleGuard } from "@/components/auth/role-guard";
import { StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";

type SuperAdminPlaceholderPageProps = {
  title: string;
  description: string;
  message: string;
  icon: LucideIcon;
};

export function SuperAdminPlaceholderPage({
  title,
  description,
  message,
  icon: Icon,
}: SuperAdminPlaceholderPageProps) {
  return (
    <RoleGuard allowedRoles={["superadmin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Super Admin"
            title={title}
            description={description}
          />

          <AppCard>
            <AppCardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <AppCardTitle>{title}</AppCardTitle>
                    <AppCardDescription className="mt-1">
                      {message}
                    </AppCardDescription>
                  </div>
                </div>
                <StatusBadge tone="neutral">Preparacion</StatusBadge>
              </div>
            </AppCardHeader>
            <AppCardContent className="text-sm leading-6 text-muted-foreground">
              Esta vista queda disponible en la navegacion global mientras se
              define el contrato web y las metricas operativas del modulo.
            </AppCardContent>
          </AppCard>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
