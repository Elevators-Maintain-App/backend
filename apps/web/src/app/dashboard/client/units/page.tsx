"use client";

import { ArrowLeft, ChevronLeft, ChevronRight, Package } from "lucide-react";
import Link from "next/link";
import { useDeferredValue, useState } from "react";
import { RoleGuard } from "@/components/auth/role-guard";
import { ClientUnitCard } from "@/components/client/client-unit-card";
import { EmptyState, ErrorState } from "@/components/feedback";
import { AppInput } from "@/components/forms";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useClientUnits } from "@/hooks/use-client-units";

const pageSize = 10;

export default function ClientUnitsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search.trim());

  const unitsQuery = useClientUnits({
    page,
    page_size: pageSize,
    search: deferredSearch || undefined
  });
  const unitsPage = unitsQuery.data;

  return (
    <RoleGuard allowedRoles={["client"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Cliente"
            title="Unidades"
            description="Unidades asociadas a tu cliente."
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
            <AppCardContent>
              <AppInput
                label="Buscar"
                placeholder="Unidad o proyecto"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
            </AppCardContent>
          </AppCard>

          {unitsQuery.isLoading ? (
            <AppCard>
              <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
                <Package className="h-5 w-5 animate-pulse text-primary" />
                Cargando unidades...
              </AppCardContent>
            </AppCard>
          ) : null}

          {unitsQuery.isError ? (
            <ErrorState
              description="No fue posible cargar tus unidades."
              onRetry={() => void unitsQuery.refetch()}
            />
          ) : null}

          {!unitsQuery.isLoading && !unitsQuery.isError && !unitsPage?.data.length ? (
            <EmptyState
              title="No encontramos unidades"
              description="Ajusta la busqueda o vuelve a intentarlo mas tarde."
            />
          ) : null}

          {unitsPage?.data.length ? (
            <>
              <section className="grid items-start grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                {unitsPage.data.map((unit) => (
                  <ClientUnitCard key={unit.id} unit={unit} />
                ))}
              </section>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Pagina {unitsPage.page} de {unitsPage.total_pages || 1} ({unitsPage.total} unidades)
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
                    disabled={page >= unitsPage.total_pages}
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
