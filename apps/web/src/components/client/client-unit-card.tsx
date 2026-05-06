"use client";

import {
  AlertCircle,
  ArrowUpRight,
  Building2,
  ChevronDown,
  Settings2,
  ShieldCheck
} from "lucide-react";
import Link from "next/link";
import { useId, useState } from "react";
import { AppButton } from "@/components/ui/app-button";
import { cn } from "@/lib/utils";
import type { ClientUnit } from "@/types/client-portal";

type ClientUnitCardProps = {
  unit: ClientUnit;
};

type UnitStatus = {
  label: string;
  tone: string;
  glow: string;
  track: string;
};

function parseKpi(kpi: string | null) {
  if (!kpi) {
    return null;
  }

  const match = kpi.match(/\d+/);
  if (!match) {
    return null;
  }

  const value = Number(match[0]);
  if (Number.isNaN(value)) {
    return null;
  }

  return Math.max(0, Math.min(100, value));
}

function getUnitStatus(kpi: number | null): UnitStatus {
  if (kpi === null) {
    return {
      label: "Observacion",
      tone: "bg-warning/15 text-warning",
      glow: "shadow-[0_0_0_1px_rgba(245,158,11,0.10)]",
      track: "stroke-warning"
    };
  }

  if (kpi >= 85) {
    return {
      label: "Operativo",
      tone: "bg-success/15 text-success",
      glow: "shadow-[0_0_18px_rgba(22,163,74,0.16)]",
      track: "stroke-success"
    };
  }

  if (kpi >= 70) {
    return {
      label: "Observacion",
      tone: "bg-warning/15 text-warning",
      glow: "shadow-[0_0_0_1px_rgba(245,158,11,0.10)]",
      track: "stroke-warning"
    };
  }

  if (kpi >= 45) {
    return {
      label: "Critico",
      tone: "bg-destructive/10 text-destructive",
      glow: "shadow-[0_0_0_1px_rgba(220,38,38,0.10)]",
      track: "stroke-destructive"
    };
  }

  return {
    label: "Detenido",
    tone: "bg-secondary/10 text-secondary",
    glow: "shadow-[0_0_0_1px_rgba(30,41,59,0.10)]",
    track: "stroke-secondary"
  };
}

function KpiRing({
  value,
  trackClassName
}: {
  value: number | null;
  trackClassName: string;
}) {
  const size = 72;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = value ?? 0;
  const offset = circumference - (normalizedValue / 100) * circumference;

  return (
    <div className="relative flex h-[72px] w-[72px] items-center justify-center">
      <svg className="-rotate-90" width={size} height={size} aria-hidden="true">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className="fill-none stroke-muted"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn("fill-none transition-all duration-300", trackClassName)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-sm font-semibold text-foreground">
          {value !== null ? `${value}%` : "--"}
        </p>
        <p className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          KPI
        </p>
      </div>
    </div>
  );
}

export function ClientUnitCard({ unit }: ClientUnitCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const detailsId = useId();
  const kpiValue = parseKpi(unit.kpi_functioning);
  const status = getUnitStatus(kpiValue);

  return (
    <article className="group overflow-hidden rounded-3xl border border-border bg-card shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary/20 hover:shadow-xl">
      <button
        type="button"
        onClick={() => setIsExpanded((value) => !value)}
        aria-expanded={isExpanded}
        aria-controls={detailsId}
        className="block w-full text-left"
      >
        <div className="relative h-44 overflow-hidden border-b border-border/70 bg-gradient-to-br from-secondary/95 via-secondary to-primary/70">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.18),transparent_28%),linear-gradient(135deg,rgba(255,255,255,0.06),transparent_58%)]" />
          <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-secondary/35 to-transparent" />

          <div className="absolute right-4 top-4">
            <span
              className={cn(
                "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium backdrop-blur-sm",
                status.tone,
                status.glow
              )}
            >
              <span className="h-2 w-2 rounded-full bg-current" />
              {status.label}
            </span>
          </div>

          <div className="relative flex h-full items-end justify-between px-5 py-5">
            <div className="space-y-2 text-white">
              <div className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-sm">
                <Settings2 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-white/70">
                  Transporte vertical
                </p>
                <h3 className="max-w-[14rem] text-lg font-semibold tracking-tight">
                  {unit.name}
                </h3>
              </div>
            </div>

            <div className="hidden rounded-2xl border border-white/10 bg-white/10 p-2 backdrop-blur-sm sm:block">
              <ShieldCheck className="h-5 w-5 text-white/90" />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 p-5">
          <div className="min-w-0 flex-1">
            <p className="truncate text-lg font-semibold tracking-tight text-foreground">
              {unit.name}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Toca para ver informacion de la unidad
            </p>
          </div>

          <div className="flex items-center gap-3">
            <KpiRing value={kpiValue} trackClassName={status.track} />
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-muted/45 text-muted-foreground transition-colors group-hover:bg-primary/10 group-hover:text-primary">
              <ChevronDown
                className={cn(
                  "h-5 w-5 transition-transform duration-300",
                  isExpanded ? "rotate-180" : ""
                )}
              />
            </div>
          </div>
        </div>
      </button>

      <div
        id={detailsId}
        className={cn(
          "grid overflow-hidden transition-all duration-300",
          isExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
        )}
      >
        <div className="min-h-0">
          <div className="space-y-4 border-t border-border/70 px-5 pb-5 pt-4">
            <div className="grid gap-3 text-sm sm:grid-cols-2">
              <div className="px-1">
                <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Proyecto / cliente
                </p>
                <p className="mt-1 flex items-center gap-2 font-medium text-foreground">
                  <Building2 className="h-4 w-4 text-primary" />
                  <span className="truncate">{unit.project}</span>
                </p>
              </div>
              <div className="px-1">
                <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Marca / modelo
                </p>
                <p className="mt-1 font-medium text-foreground">
                  {unit.type || "Sin especificar"}
                </p>
              </div>
              <div className="px-1 sm:col-span-2">
                <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Ultima intervencion
                </p>
                <p className="mt-1 font-medium text-foreground">
                  Sin registro reciente
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <div onClick={(event) => event.stopPropagation()}>
                <AppButton asChild size="sm" className="w-full rounded-xl px-3.5 sm:w-auto">
                  <Link href={`/dashboard/client/units/${unit.id}`}>
                    Ver detalle
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                </AppButton>
              </div>

              <div onClick={(event) => event.stopPropagation()}>
                <AppButton
                  asChild
                  variant="outline"
                  size="sm"
                  className="w-full rounded-xl px-3.5 sm:w-auto"
                >
                  <Link href="/dashboard/client/orders">
                    <AlertCircle className="h-4 w-4" />
                    Reportar incidencia
                  </Link>
                </AppButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
