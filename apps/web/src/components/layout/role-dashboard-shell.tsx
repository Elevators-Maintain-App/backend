"use client";

import { Hammer, UserRound } from "lucide-react";
import { StatusBadge } from "@/components/feedback/status-badge";
import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "@/hooks/use-auth";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";

type RoleDashboardShellProps = {
  title: string;
  description: string;
  roleLabel: string;
};

export function RoleDashboardShell({
  title,
  description,
  roleLabel
}: RoleDashboardShellProps) {
  const { userProfile } = useAuth();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Dashboard"
        title={title}
        description={description}
      />

      <section className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <AppCard>
          <AppCardHeader>
            <StatusBadge tone="info">{roleLabel}</StatusBadge>
            <AppCardTitle className="pt-3">Modulo en construccion</AppCardTitle>
            <AppCardDescription>
              Esta vista es un placeholder para validar autenticacion, routing
              protegido y experiencia por rol antes de conectar datos reales.
            </AppCardDescription>
          </AppCardHeader>
          <AppCardContent className="text-sm leading-6 text-muted-foreground">
            Aqui iremos montando los modulos operativos del rol una vez exista
            el contrato `/api/web/*` correspondiente.
          </AppCardContent>
        </AppCard>

        <AppCard>
          <AppCardHeader>
            <UserRound className="h-5 w-5 text-primary" />
            <AppCardTitle className="pt-3">Usuario actual</AppCardTitle>
          </AppCardHeader>
          <AppCardContent className="space-y-3 text-sm">
            <p>
              <span className="font-medium text-foreground">Correo:</span>{" "}
              <span className="text-muted-foreground">
                {userProfile?.email || "No disponible"}
              </span>
            </p>
            <p>
              <span className="font-medium text-foreground">UID:</span>{" "}
              <span className="break-all text-muted-foreground">
                {userProfile?.uid || "No disponible"}
              </span>
            </p>
            <p>
              <span className="font-medium text-foreground">Rol detectado:</span>{" "}
              <span className="text-muted-foreground">
                {userProfile?.rawRole || "No disponible"}
              </span>
            </p>
            <p>
              <span className="font-medium text-foreground">
                Rol normalizado:
              </span>{" "}
              <span className="text-muted-foreground">
                {userProfile?.role || "No disponible"}
              </span>
            </p>
          </AppCardContent>
        </AppCard>
      </section>

      <AppCard>
        <AppCardHeader>
          <Hammer className="h-5 w-5 text-primary" />
          <AppCardTitle className="pt-3">Siguiente etapa</AppCardTitle>
        </AppCardHeader>
        <AppCardContent className="text-sm leading-6 text-muted-foreground">
          El siguiente paso sera conectar navegacion de modulos, filtros y datos
          reales sin salirnos de endpoints `/api/web/*`.
        </AppCardContent>
      </AppCard>
    </div>
  );
}
