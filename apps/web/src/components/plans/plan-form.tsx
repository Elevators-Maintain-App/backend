"use client";

import { useMemo, useState } from "react";
import type { FormEvent } from "react";
import { AlertTriangle } from "lucide-react";
import { AppInput } from "@/components/forms";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import type { Plan, PlanFeatures, PlanFormValues, PlanLimits } from "@/types/plans";

type LimitKey = keyof PlanLimits;
type FeatureKey = keyof PlanFeatures;

const limitFields: Array<{ key: LimitKey; label: string; hint?: string }> = [
  { key: "admins", label: "Admins" },
  { key: "supervisors", label: "Supervisores" },
  { key: "technicians", label: "Técnicos" },
  { key: "projects", label: "Proyectos" },
  { key: "clients", label: "Clientes" },
  { key: "units", label: "Unidades" },
  { key: "work_orders_per_month", label: "Órdenes/mes" },
  { key: "pdf_reports_per_month", label: "PDFs/mes" },
  { key: "storage_mb", label: "Storage MB" },
];

const featureFields: Array<{ key: FeatureKey; label: string }> = [
  { key: "offline_mode", label: "Modo offline" },
  { key: "custom_checklists", label: "Checklists personalizados" },
  { key: "advanced_dashboard", label: "Dashboard avanzado" },
  { key: "evidence_editing", label: "Edición de evidencias" },
];

const emptyLimits: PlanLimits = {
  admins: null,
  supervisors: null,
  technicians: null,
  projects: null,
  clients: null,
  units: null,
  work_orders_per_month: null,
  pdf_reports_per_month: null,
  storage_mb: null,
};

const emptyFeatures: PlanFeatures = {
  offline_mode: false,
  custom_checklists: false,
  advanced_dashboard: false,
  evidence_editing: false,
};

type PlanFormProps = {
  plan?: Plan | null;
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onCancel: () => void;
  onSubmit: (values: PlanFormValues) => Promise<void> | void;
};

export function buildPlanFormValues(plan?: Plan | null): PlanFormValues {
  return {
    code: plan?.code || "",
    name: plan?.name || "",
    description: plan?.description || "",
    is_public: plan?.is_public ?? true,
    is_active: plan?.is_active ?? true,
    limits: {
      ...emptyLimits,
      ...(plan?.limits || {}),
    },
    features: {
      ...emptyFeatures,
      ...(plan?.features || {}),
    },
  };
}

function toLimitInputs(limits: PlanLimits) {
  return Object.fromEntries(
    limitFields.map(({ key }) => [key, limits[key] === null ? "" : String(limits[key])])
  ) as Record<LimitKey, string>;
}

function parseLimit(value: string) {
  if (value.trim() === "") {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
}

export function formatLimit(value: number | null | undefined) {
  return value === null || value === undefined ? "Sin límite" : String(value);
}

export function PlanForm({
  plan,
  isSubmitting = false,
  errorMessage,
  onCancel,
  onSubmit,
}: PlanFormProps) {
  const initialValues = useMemo(() => buildPlanFormValues(plan), [plan]);
  const [values, setValues] = useState(initialValues);
  const [limitInputs, setLimitInputs] = useState(() => toLimitInputs(initialValues.limits));
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!values.code.trim() || !values.name.trim()) {
      setValidationError("Código y nombre son obligatorios.");
      return;
    }

    const parsedLimits = Object.fromEntries(
      limitFields.map(({ key }) => [key, parseLimit(limitInputs[key])])
    ) as PlanLimits;

    const hasInvalidLimit = Object.values(parsedLimits).some(
      (value) => Number.isNaN(value) || (typeof value === "number" && value < 0)
    );

    if (hasInvalidLimit) {
      setValidationError("Los límites deben estar vacíos o ser números mayores o iguales a 0.");
      return;
    }

    setValidationError(null);
    await onSubmit({
      ...values,
      code: values.code.trim(),
      name: values.name.trim(),
      description: values.description.trim(),
      limits: parsedLimits,
    });
  };

  return (
    <AppCard>
      <AppCardHeader>
        <AppCardTitle>{plan ? "Editar plan" : "Crear plan"}</AppCardTitle>
      </AppCardHeader>
      <AppCardContent>
        <form className="space-y-6" onSubmit={handleSubmit}>
          {(validationError || errorMessage) ? (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{validationError || errorMessage}</span>
            </div>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            <AppInput
              label="Código"
              value={values.code}
              onChange={(event) => setValues((current) => ({ ...current, code: event.target.value }))}
              placeholder="professional"
            />
            <AppInput
              label="Nombre"
              value={values.name}
              onChange={(event) => setValues((current) => ({ ...current, name: event.target.value }))}
              placeholder="Professional"
            />
            <AppInput
              label="Descripción"
              value={values.description}
              onChange={(event) => setValues((current) => ({ ...current, description: event.target.value }))}
              className="lg:col-span-2"
              placeholder="Plan para operación técnica en crecimiento"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex items-center gap-3 rounded-lg border bg-background p-3 text-sm">
              <input
                type="checkbox"
                checked={values.is_public}
                onChange={(event) => setValues((current) => ({ ...current, is_public: event.target.checked }))}
              />
              Público
            </label>
            <label className="flex items-center gap-3 rounded-lg border bg-background p-3 text-sm">
              <input
                type="checkbox"
                checked={values.is_active}
                onChange={(event) => setValues((current) => ({ ...current, is_active: event.target.checked }))}
              />
              Activo
            </label>
          </div>

          <section className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Límites</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Deja un campo vacío para marcarlo como sin límite.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {limitFields.map((field) => (
                <AppInput
                  key={field.key}
                  label={field.label}
                  type="number"
                  min={0}
                  value={limitInputs[field.key]}
                  onChange={(event) =>
                    setLimitInputs((current) => ({
                      ...current,
                      [field.key]: event.target.value,
                    }))
                  }
                  placeholder="Sin límite"
                />
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground">Features</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {featureFields.map((field) => (
                <label key={field.key} className="flex items-center gap-3 rounded-lg border bg-background p-3 text-sm">
                  <input
                    type="checkbox"
                    checked={values.features[field.key]}
                    onChange={(event) =>
                      setValues((current) => ({
                        ...current,
                        features: {
                          ...current.features,
                          [field.key]: event.target.checked,
                        },
                      }))
                    }
                  />
                  {field.label}
                </label>
              ))}
            </div>
          </section>

          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <AppButton type="button" variant="outline" onClick={onCancel}>
              Cancelar
            </AppButton>
            <AppButton type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando..." : plan ? "Guardar cambios" : "Crear plan"}
            </AppButton>
          </div>
        </form>
      </AppCardContent>
    </AppCard>
  );
}
