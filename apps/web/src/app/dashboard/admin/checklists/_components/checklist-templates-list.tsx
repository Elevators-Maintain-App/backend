"use client";

import { ChevronDown, ChevronUp, ClipboardList, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { EmptyState, ErrorState } from "@/components/feedback";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import { AppButton } from "@/components/ui/app-button";
import { cn } from "@/lib/utils";
import type { ChecklistTemplateAdmin } from "@/types/checklists";

type ChecklistTemplatesListProps = {
  templates: ChecklistTemplateAdmin[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  focusedTemplateId: string | null;
};

function catalogLabel(name: string | null, id: number) {
  return name ? `${name} (ID ${id})` : `No encontrado (ID ${id})`;
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "No disponible";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "No disponible";
  }

  return new Intl.DateTimeFormat("es-PA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function ChecklistTemplatesList({
  templates,
  isLoading,
  isError,
  onRetry,
  focusedTemplateId,
}: ChecklistTemplatesListProps) {
  const [expandedTemplateIds, setExpandedTemplateIds] = useState<string[]>([]);
  const templateRefs = useRef<Record<string, HTMLLIElement | null>>({});

  useEffect(() => {
    if (!focusedTemplateId) {
      return;
    }

    setExpandedTemplateIds((current) =>
      current.includes(focusedTemplateId) ? current : [...current, focusedTemplateId]
    );
    templateRefs.current[focusedTemplateId]?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [focusedTemplateId]);

  if (isLoading) {
    return (
      <AppCard>
        <AppCardContent className="flex items-center gap-3 py-8 text-sm text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
          Cargando plantillas existentes…
        </AppCardContent>
      </AppCard>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="No pudimos cargar las plantillas"
        description="Puedes seguir preparando un JSON, pero no será posible comprobar previamente si la combinación ya existe."
        onRetry={onRetry}
      />
    );
  }

  if (!templates?.length) {
    return (
      <EmptyState
        title="No hay plantillas creadas"
        description="Carga la primera plantilla JSON para una combinación de tipo de orden y unidad."
      />
    );
  }

  return (
    <ul className="space-y-4" aria-label="Plantillas de checklist existentes">
      {templates.map((template) => {
        const isExpanded = expandedTemplateIds.includes(template.id);
        const isFocused = focusedTemplateId === template.id;

        return (
          <li
            key={template.id}
            ref={(element) => {
              templateRefs.current[template.id] = element;
            }}
          >
            <AppCard className={cn(isFocused && "border-primary ring-1 ring-primary/30")}>
              <AppCardHeader className="gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <ClipboardList className="h-4 w-4 text-primary" aria-hidden="true" />
                    <AppCardTitle>{template.nombre}</AppCardTitle>
                  </div>
                  <AppCardDescription className="mt-2">
                    {catalogLabel(template.tipo_orden_nombre, template.tipo_orden_id)} · {" "}
                    {catalogLabel(template.tipo_unidad_nombre, template.tipo_unidad_id)}
                  </AppCardDescription>
                </div>
                <AppButton
                  type="button"
                  variant="outline"
                  aria-expanded={isExpanded}
                  aria-controls={`checklist-template-steps-${template.id}`}
                  onClick={() => {
                    setExpandedTemplateIds((current) =>
                      current.includes(template.id)
                        ? current.filter((id) => id !== template.id)
                        : [...current, template.id]
                    );
                  }}
                >
                  {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {isExpanded ? "Ocultar pasos" : "Ver pasos"}
                </AppButton>
              </AppCardHeader>
              <AppCardContent className="space-y-4">
                <dl className="grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-muted-foreground">Pasos</dt>
                    <dd className="mt-1 font-medium">{template.total_steps}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Creada</dt>
                    <dd className="mt-1 font-medium">{formatTimestamp(template.created_at)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Actualizada</dt>
                    <dd className="mt-1 font-medium">{formatTimestamp(template.updated_at)}</dd>
                  </div>
                </dl>

                {isExpanded ? (
                  <ol id={`checklist-template-steps-${template.id}`} className="space-y-3">
                    {template.pasos.map((step) => (
                      <li key={step.id} className="rounded-md border p-4">
                        <h3 className="font-medium">
                          Paso {step.step_number}: {step.titulo}
                        </h3>
                        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                          {step.instrucciones}
                        </p>
                        <div className="mt-3">
                          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                            Esquema de evidencia
                          </p>
                          <pre className="mt-1 max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs leading-5 text-foreground">
                            {JSON.stringify(step.evidencia_schema, null, 2)}
                          </pre>
                        </div>
                      </li>
                    ))}
                  </ol>
                ) : null}
              </AppCardContent>
            </AppCard>
          </li>
        );
      })}
    </ul>
  );
}
