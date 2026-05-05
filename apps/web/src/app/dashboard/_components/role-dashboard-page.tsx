"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { AppShell } from "@/components/layout/app-shell";
import { RoleDashboardShell } from "@/components/layout/role-dashboard-shell";
import type { NormalizedUserRole } from "@/types/auth";

type RoleDashboardPageProps = {
  role: NormalizedUserRole;
  title: string;
  description: string;
  roleLabel: string;
};

export function RoleDashboardPage({
  role,
  title,
  description,
  roleLabel
}: RoleDashboardPageProps) {
  return (
    <RoleGuard allowedRoles={[role]}>
      <AppShell>
        <RoleDashboardShell
          title={title}
          description={description}
          roleLabel={roleLabel}
        />
      </AppShell>
    </RoleGuard>
  );
}
