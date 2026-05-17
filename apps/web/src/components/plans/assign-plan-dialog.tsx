"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { AlertTriangle, X } from "lucide-react";
import { AppInput, AppSelect } from "@/components/forms";
import { AppButton } from "@/components/ui/app-button";
import type { AssignPlanPayload, CompanySubscriptionStatus, Plan, SuperAdminCompany } from "@/types/plans";

type AssignPlanDialogProps = {
  company: SuperAdminCompany;
  plans: Plan[];
  currentStatus?: CompanySubscriptionStatus | null;
  errorMessage?: string | null;
  isSubmitting?: boolean;
  onClose: () => void;
  onSubmit: (payload: AssignPlanPayload) => Promise<void> | void;
};

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export function AssignPlanDialog({
  company,
  plans,
  currentStatus,
  errorMessage,
  isSubmitting = false,
  onClose,
  onSubmit,
}: AssignPlanDialogProps) {
  const activePlans = plans.filter((plan) => plan.is_active);
  const [planId, setPlanId] = useState(currentStatus?.plan?.id || activePlans[0]?.id || "");
  const [status, setStatus] = useState("active");
  const [billingPeriod, setBillingPeriod] = useState("monthly");
  const [startDate, setStartDate] = useState(todayIsoDate());
  const [endDate, setEndDate] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!planId) {
      setValidationError("Selecciona un plan.");
      return;
    }
    if (!startDate) {
      setValidationError("La fecha de inicio es obligatoria.");
      return;
    }
    if (endDate && endDate < startDate) {
      setValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.");
      return;
    }

    setValidationError(null);
    await onSubmit({
      plan_id: planId,
      status,
      billing_period: billingPeriod,
      start_date: startDate,
      end_date: endDate || null,
    });
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-background/80 px-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-lg border bg-card p-5 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-primary">Cambiar plan</p>
            <h2 className="mt-1 text-xl font-semibold text-foreground">{company.name}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Plan actual: {currentStatus?.plan?.name || "Sin suscripción activa"}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          {(validationError || errorMessage) ? (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{validationError || errorMessage}</span>
            </div>
          ) : null}

          <AppSelect
            label="Nuevo plan"
            value={planId}
            onChange={(event) => setPlanId(event.target.value)}
            options={activePlans.map((plan) => ({ value: plan.id, label: `${plan.name} (${plan.code})` }))}
            placeholder="Seleccionar plan"
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <AppSelect
              label="Estado"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              options={[
                { value: "active", label: "Activa" },
                { value: "trial", label: "Trial" },
                { value: "trialing", label: "Trialing" },
                { value: "past_due", label: "Pago pendiente" },
                { value: "suspended", label: "Suspendida" },
                { value: "cancelled", label: "Cancelada" },
              ]}
            />
            <AppSelect
              label="Periodo"
              value={billingPeriod}
              onChange={(event) => setBillingPeriod(event.target.value)}
              options={[
                { value: "monthly", label: "Mensual" },
                { value: "yearly", label: "Anual" },
                { value: "pilot", label: "Piloto" },
                { value: "custom", label: "Personalizado" },
              ]}
            />
            <AppInput
              label="Inicio"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
            <AppInput
              label="Fin opcional"
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </div>

          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <AppButton type="button" variant="outline" onClick={onClose}>
              Cancelar
            </AppButton>
            <AppButton type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando..." : "Guardar asignación"}
            </AppButton>
          </div>
        </form>
      </div>
    </div>
  );
}
