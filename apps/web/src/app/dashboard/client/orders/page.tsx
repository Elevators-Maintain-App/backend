"use client";

import { ArrowLeft, ChevronLeft, ChevronRight, ClipboardList, Eye } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useEffect, useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { DataTable } from "@/components/data-display";
import { EmptyState, ErrorState, StatusBadge } from "@/components/feedback";
import { AppInput, AppSelect } from "@/components/forms";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useClientOrders } from "@/hooks/use-client-orders";
import type { ClientOrder } from "@/types/client-portal";

const pageSize = 10;

function statusTone(status: string) {
  return status === "Cerrada" ? "success" : "warning";
}

export default function ClientOrdersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const deferredSearch = useDeferredValue(search.trim());

  useEffect(() => {
    const initialStatus = new URLSearchParams(window.location.search).get("status");
    if (initialStatus) {
      setStatus(initialStatus);
    }
  }, []);

  const ordersQuery = useClientOrders({
    page,
    page_size: pageSize,
    search: deferredSearch || undefined,
    status: status || undefined
  });
  const ordersPage = ordersQuery.data;

  const columns = [
    {
      key: "order",
      header: "Orden",
      cell: (order: ClientOrder) => (
        <div className="min-w-0">
          <p className="truncate font-medium">{order.reference || "Sin referencia"}</p>
          <p className="truncate text-xs text-muted-foreground">
            {order.project} / {order.unit}
          </p>
        </div>
      )
    },
    {
      key: "status",
      header: "Estado",
      cell: (order: ClientOrder) => (
        <StatusBadge tone={statusTone(order.status)}>{order.status}</StatusBadge>
      )
    },
    {
      key: "date",
      header: "Fecha",
      cell: (order: ClientOrder) => order.date || "Sin fecha"
    },
    {
      key: "report",
      header: "Reporte",
      cell: (order: ClientOrder) => (
        <StatusBadge tone={order.has_report ? "success" : "neutral"}>
          {order.has_report ? "Disponible" : "No disponible"}
        </StatusBadge>
      )
    },
    {
      key: "actions",
      header: "Acciones",
      cell: (order: ClientOrder) => (
        <AppButton asChild variant="outline" size="sm">
          <Link href={`/dashboard/client/orders/${order.id}`}>
            <Eye className="h-4 w-4" />
            Ver
          </Link>
        </AppButton>
      )
    }
  ];

  return (
    <RoleGuard allowedRoles={["client"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Cliente"
            title="Ordenes"
            description="Ordenes visibles para tu cliente asociado."
            actions={
              <AppButton asChild variant="outline">
                <Link href="/dashboard/client">
                  <ArrowLeft className="h-4 w-4" />
                  Volver
                </Link>
              </AppButton>
            }
          />

          <AppCard>
            <AppCardHeader>
              <AppCardTitle>Filtros</AppCardTitle>
            </AppCardHeader>
            <AppCardContent className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
              <AppInput
                label="Buscar"
                placeholder="Referencia, proyecto o unidad"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <AppSelect
                label="Estado"
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setPage(1);
                }}
                placeholder="Todos"
                options={[
                  { value: "Cerrada", label: "Cerrada" },
                  { value: "En ejecucion", label: "En ejecucion" },
                  { value: "Pendiente", label: "Pendiente" },
                  { value: "Completada", label: "Completada" }
                ]}
              />
            </AppCardContent>
          </AppCard>

          {ordersQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <ClipboardList className="h-5 w-5 animate-pulse text-primary" />
                Cargando ordenes...
              </AppCardContent>
            </AppCard>
          ) : null}

          {ordersQuery.isError ? (
            <ErrorState
              description="No fue posible cargar tus ordenes."
              onRetry={() => void ordersQuery.refetch()}
            />
          ) : null}

          {!ordersQuery.isLoading && !ordersQuery.isError && !ordersPage?.data.length ? (
            <EmptyState
              title="No encontramos ordenes"
              description="Ajusta la busqueda o el filtro de estado para intentar de nuevo."
            />
          ) : null}

          {ordersPage?.data.length ? (
            <>
              <DataTable columns={columns} data={ordersPage.data} getRowKey={(order) => order.id} />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Pagina {ordersPage.page} de {ordersPage.total_pages || 1} ({ordersPage.total} ordenes)
                </p>
                <div className="flex gap-2">
                  <AppButton
                    variant="outline"
                    disabled={page <= 1}
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                  </AppButton>
                  <AppButton
                    variant="outline"
                    disabled={page >= ordersPage.total_pages}
                    onClick={() => setPage((current) => current + 1)}
                  >
                    Siguiente
                    <ChevronRight className="h-4 w-4" />
                  </AppButton>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </AppShell>
    </RoleGuard>
  );
}
