"use client";

import { RoleGuard } from "@/components/auth/role-guard";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/layout/page-header";
import { useChecklistTemplates } from "@/hooks/use-checklist-templates";
import { useState } from "react";
import { ChecklistTemplateUpload } from "./_components/checklist-template-upload";
import { ChecklistTemplatesList } from "./_components/checklist-templates-list";

export default function AdminChecklistsPage() {
  const [focusedTemplateId, setFocusedTemplateId] = useState<string | null>(null);
  const checklistTemplates = useChecklistTemplates();

  return (
    <RoleGuard allowedRoles={["admin"]}>
      <AppShell>
        <div className="flex flex-col gap-6">
          <PageHeader
            eyebrow="Administración"
            title="Checklists"
            description="Carga una plantilla JSON, revisa sus pasos y créala para una combinación de tipo de orden y unidad."
          />
          <section className="space-y-4" aria-labelledby="existing-templates-title">
            <div>
              <h2 id="existing-templates-title" className="text-xl font-semibold">
                Plantillas existentes
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Revisa qué plantilla ocupa cada combinación antes de cargar una nueva.
              </p>
            </div>
            <ChecklistTemplatesList
              templates={checklistTemplates.data}
              isLoading={checklistTemplates.isLoading}
              isError={checklistTemplates.isError}
              onRetry={() => void checklistTemplates.refetch()}
              focusedTemplateId={focusedTemplateId}
            />
          </section>

          <section className="space-y-4" aria-labelledby="upload-template-title">
            <div>
              <h2 id="upload-template-title" className="text-xl font-semibold">
                Cargar nueva plantilla
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Selecciona un JSON para validarlo y comprobar su combinación antes de enviarlo.
              </p>
            </div>
            <ChecklistTemplateUpload
              existingTemplates={checklistTemplates.data || []}
              isTemplatesLoading={checklistTemplates.isLoading}
              hasTemplatesError={checklistTemplates.isError}
              onShowExistingTemplate={setFocusedTemplateId}
            />
          </section>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
