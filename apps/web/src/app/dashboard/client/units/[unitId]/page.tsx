"use client";

import { ArrowLeft, Building2, Package } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { RoleGuard } from "@/components/auth/role-guard";
import { ErrorState, StatusBadge } from "@/components/feedback";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useClientUnitDetail } from "@/hooks/use-client-units";

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="break-words text-sm">{value || "No disponible"}</p>
    </div>
  );
}

export default function ClientUnitDetailPage() {
  const params = useParams<{ unitId: string }>();
  const unitQuery = useClientUnitDetail(params.unitId);
  const unit = unitQuery.data;

  return (
    <RoleGuard allowedRoles={["client"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Cliente"
            title={unit?.name || "Detalle de unidad"}
            description="Informacion visible de la unidad seleccionada."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/client/units">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          {unitQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <Package className="h-5 w-5 animate-pulse text-primary" />
                Cargando unidad...
              </AppCardContent>
            </AppCard>
          ) : null}

          {unitQuery.isError ? (
            <ErrorState
              description="No fue posible cargar la unidad solicitada."
              onRetry={() => void unitQuery.refetch()}
            />
          ) : null}

          {unit ? (
            <AppCard>
              <AppCardHeader>
                <div className="flex items-center justify-between gap-3">
                  <AppCardTitle>Informacion general</AppCardTitle>
                  <StatusBadge tone="neutral">{unit.type || "Sin tipo"}</StatusBadge>
                </div>
              </AppCardHeader>
              <AppCardContent className="grid gap-5 md:grid-cols-2">
                <DetailRow label="Proyecto" value={unit.project} />
                <DetailRow label="KPI funcionamiento" value={unit.kpi_functioning} />
                <DetailRow label="Unidad ID" value={unit.id} />
                <DetailRow label="Proyecto ID" value={unit.project_id} />
                <div className="flex items-center gap-2 rounded-md border bg-muted/40 p-3 text-sm text-muted-foreground md:col-span-2">
                  <Building2 className="h-4 w-4 text-primary" />
                  Esta unidad se muestra porque pertenece al cliente asociado a tu usuario.
                </div>
              </AppCardContent>
            </AppCard>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
