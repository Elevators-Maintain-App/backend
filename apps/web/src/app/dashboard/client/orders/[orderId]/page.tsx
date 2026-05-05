"use client";

import { ArrowLeft, ClipboardList, ExternalLink } from "lucide-react";
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
import {
  useClientOrderDetail,
  useClientOrderReport
} from "@/hooks/use-client-orders";

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium uppercase text-muted-foreground">{label}</p>
      <p className="break-words text-sm">{value || "No disponible"}</p>
    </div>
  );
}

function statusTone(status?: string) {
  return status === "Cerrada" ? "success" : "warning";
}

export default function ClientOrderDetailPage() {
  const params = useParams<{ orderId: string }>();
  const orderQuery = useClientOrderDetail(params.orderId);
  const order = orderQuery.data;
  const canViewReport = Boolean(
    order && order.status === "Cerrada" && order.has_report
  );
  const reportQuery = useClientOrderReport(params.orderId, canViewReport);

  return (
    <RoleGuard allowedRoles={["client"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Cliente"
            title={order?.reference || "Detalle de orden"}
            description="Informacion visible de la orden seleccionada."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/client/orders">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          {orderQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <ClipboardList className="h-5 w-5 animate-pulse text-primary" />
                Cargando orden...
              </AppCardContent>
            </AppCard>
          ) : null}

          {orderQuery.isError ? (
            <ErrorState
              description="No fue posible cargar la orden solicitada."
              onRetry={() => void orderQuery.refetch()}
            />
          ) : null}

          {order ? (
            <>
              <AppCard>
                <AppCardHeader>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <AppCardTitle>Informacion general</AppCardTitle>
                    <div className="flex flex-wrap gap-2">
                      <StatusBadge tone={statusTone(order.status)}>{order.status}</StatusBadge>
                      {order.priority ? (
                        <StatusBadge tone="neutral">{order.priority}</StatusBadge>
                      ) : null}
                    </div>
                  </div>
                </AppCardHeader>
                <AppCardContent className="grid gap-5 md:grid-cols-2">
                  <DetailRow label="Proyecto" value={order.project} />
                  <DetailRow label="Unidad" value={order.unit} />
                  <DetailRow label="Fecha" value={order.date} />
                  <DetailRow label="Tipo de orden" value={order.type} />
                  <DetailRow label="Tecnico" value={order.technician} />
                  <DetailRow label="Supervisor" value={order.supervisor} />
                  <DetailRow label="Descripcion" value={order.description} />
                  <DetailRow label="Observaciones" value={order.observations} />
                </AppCardContent>
              </AppCard>

              {canViewReport ? (
                <AppCard>
                  <AppCardHeader>
                    <AppCardTitle>Reporte final</AppCardTitle>
                  </AppCardHeader>
                  <AppCardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-sm text-muted-foreground">
                      Disponible porque la orden esta cerrada y tiene reporte final.
                    </p>
                    <AppButton asChild disabled={reportQuery.isLoading || !reportQuery.data?.report_url}>
                      <a
                        href={reportQuery.data?.report_url || order.final_report_url || "#"}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ExternalLink className="h-4 w-4" />
                        Ver reporte
                      </a>
                    </AppButton>
                  </AppCardContent>
                </AppCard>
              ) : (
                <AppCard>
                  <AppCardContent className="py-6">
                    <StatusBadge tone="neutral">Reporte no disponible</StatusBadge>
                    <p className="mt-3 text-sm text-muted-foreground">
                      El reporte final solo se muestra para ordenes cerradas con reporte generado.
                    </p>
                  </AppCardContent>
                </AppCard>
              )}
            </>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
