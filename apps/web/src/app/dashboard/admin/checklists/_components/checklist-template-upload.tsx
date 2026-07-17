"use client";

import axios from "axios";
import {
  CheckCircle2,
  FileJson2,
  Loader2,
  RotateCcw,
  Upload,
} from "lucide-react";
import { useRef, useState } from "react";
import { ErrorState } from "@/components/feedback";
import { AppInput } from "@/components/forms";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle,
} from "@/components/ui/app-card";
import { AppButton } from "@/components/ui/app-button";
import { useCreateChecklistTemplate } from "@/hooks/use-checklist-templates";
import {
  checklistTemplateSchema,
  type ChecklistTemplateAdmin,
  type ChecklistTemplatePayload,
} from "@/types/checklists";

const maxFileSize = 1024 * 1024;

type ChecklistTemplateUploadProps = {
  existingTemplates: ChecklistTemplateAdmin[];
  isTemplatesLoading: boolean;
  hasTemplatesError: boolean;
  onShowExistingTemplate: (templateId: string) => void;
};

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  return `${(bytes / 1024).toFixed(1)} KiB`;
}

function getValidationMessage(error: unknown) {
  const result = checklistTemplateSchema.safeParse(error);
  if (result.success) {
    return null;
  }

  return result.error.issues[0]?.message || "El archivo no tiene el formato esperado.";
}

function getUploadErrorMessage(error: unknown, conflictTemplate: ChecklistTemplateAdmin | null) {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data as { detail?: unknown } | undefined;
    const backendMessage = typeof detail?.detail === "string" ? detail.detail : null;

    if (status === 401) {
      return "Tu sesión no está disponible o expiró. Inicia sesión nuevamente e inténtalo de nuevo.";
    }
    if (status === 403) {
      return "Tu usuario no tiene permiso para crear plantillas de checklist.";
    }
    if (status === 409) {
      if (conflictTemplate) {
        return `La plantilla "${conflictTemplate.nombre}" ya ocupa esta combinación. ${backendMessage || ""}`.trim();
      }
      return backendMessage || "Ya existe una plantilla para esa combinación de tipo de orden y unidad.";
    }
    if (status === 422) {
      return backendMessage || "El backend rechazó la plantilla. Revisa los campos e inténtalo nuevamente.";
    }
    if (!error.response) {
      return "No se pudo conectar con el servidor. Revisa tu conexión e inténtalo nuevamente.";
    }
  }

  return "No se pudo cargar la plantilla. Inténtalo nuevamente.";
}

export function ChecklistTemplateUpload({
  existingTemplates,
  isTemplatesLoading,
  hasTemplatesError,
  onShowExistingTemplate,
}: ChecklistTemplateUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [template, setTemplate] = useState<ChecklistTemplatePayload | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const createTemplate = useCreateChecklistTemplate();

  const reset = () => {
    setFile(null);
    setTemplate(null);
    setFileError(null);
    setIsConfirming(false);
    createTemplate.reset();
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    reset();

    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);
    if (selectedFile.size > maxFileSize) {
      setFileError("El archivo supera el límite de 1 MiB. Selecciona una plantilla más pequeña.");
      return;
    }

    try {
      const parsedJson: unknown = JSON.parse(await selectedFile.text());
      const validationMessage = getValidationMessage(parsedJson);
      if (validationMessage) {
        setFileError(validationMessage);
        return;
      }

      setTemplate(checklistTemplateSchema.parse(parsedJson));
    } catch (error) {
      if (error instanceof SyntaxError) {
        setFileError("El archivo no contiene JSON válido. Corrige el formato y vuelve a intentarlo.");
        return;
      }
      setFileError("No fue posible leer el archivo. Intenta seleccionarlo nuevamente.");
    }
  };

  const handleUpload = () => {
    if (!template || conflictTemplate || isTemplatesLoading) {
      return;
    }

    createTemplate.mutate(template, {
      onSuccess: () => setIsConfirming(false),
    });
  };

  const isSubmitting = createTemplate.isPending;
  const previewSteps = template ? [...template.pasos].sort((a, b) => a.step_number - b.step_number) : [];
  const conflictTemplate = template
    ? existingTemplates.find(
        (existingTemplate) =>
          existingTemplate.tipo_orden_id === template.tipo_orden_id &&
          existingTemplate.tipo_unidad_id === template.tipo_unidad_id
      ) || null
    : null;
  const isUploadBlocked = Boolean(conflictTemplate) || isTemplatesLoading;

  if (createTemplate.isSuccess && createTemplate.data) {
    return (
      <AppCard>
        <AppCardHeader>
          <div className="flex items-center gap-3 text-success">
            <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
            <div>
              <AppCardTitle>Plantilla creada</AppCardTitle>
              <AppCardDescription>
                {createTemplate.data.nombre} se cargó correctamente.
              </AppCardDescription>
            </div>
          </div>
        </AppCardHeader>
        <AppCardContent className="space-y-5">
          <dl className="grid gap-3 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-muted-foreground">ID de plantilla</dt>
              <dd className="mt-1 break-all font-medium">{createTemplate.data.id}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Pasos creados</dt>
              <dd className="mt-1 font-medium">{createTemplate.data.pasos_ids.length}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Combinación</dt>
              <dd className="mt-1 font-medium">
                Orden {createTemplate.data.tipo_orden_id} · Unidad {createTemplate.data.tipo_unidad_id}
              </dd>
            </div>
          </dl>
          <AppButton onClick={reset}>
            <RotateCcw className="h-4 w-4" />
            Cargar otra plantilla
          </AppButton>
        </AppCardContent>
      </AppCard>
    );
  }

  return (
    <div className="space-y-6">
      <AppCard>
        <AppCardHeader>
          <AppCardTitle>Archivo de plantilla</AppCardTitle>
          <AppCardDescription>
            Selecciona un único archivo JSON de hasta 1 MiB. El archivo se valida en este navegador antes de enviarlo.
          </AppCardDescription>
        </AppCardHeader>
        <AppCardContent className="space-y-4">
          <AppInput
            ref={inputRef}
            label="Archivo JSON"
            type="file"
            accept="application/json,.json"
            onChange={(event) => void handleFileChange(event)}
            disabled={isSubmitting}
            error={fileError || undefined}
          />
          {file ? (
            <div className="flex items-center justify-between gap-3 rounded-md border bg-muted/30 px-3 py-2 text-sm">
              <div className="flex min-w-0 items-center gap-2">
                <FileJson2 className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                <span className="truncate font-medium">{file.name}</span>
              </div>
              <span className="shrink-0 text-muted-foreground">{formatFileSize(file.size)}</span>
            </div>
          ) : null}
          {file || template ? (
            <AppButton type="button" variant="outline" onClick={reset} disabled={isSubmitting}>
              <RotateCcw className="h-4 w-4" />
              Limpiar archivo
            </AppButton>
          ) : null}
        </AppCardContent>
      </AppCard>

      {template ? (
        <AppCard>
          <AppCardHeader>
            <AppCardTitle>Previsualización</AppCardTitle>
            <AppCardDescription>
              Confirma los datos de la plantilla y sus pasos antes de cargarla.
            </AppCardDescription>
          </AppCardHeader>
          <AppCardContent className="space-y-6">
            <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-muted-foreground">Nombre</dt>
                <dd className="mt-1 font-medium">{template.nombre}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Tipo de orden</dt>
                <dd className="mt-1 font-medium">{template.tipo_orden_id}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Tipo de unidad</dt>
                <dd className="mt-1 font-medium">{template.tipo_unidad_id}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Total de pasos</dt>
                <dd className="mt-1 font-medium">{template.pasos.length}</dd>
              </div>
            </dl>

            <ol className="space-y-3" aria-label="Pasos de la plantilla">
              {previewSteps.map((step, index) => (
                <li key={`${step.step_number}-${index}`} className="rounded-md border p-4">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
                    <h3 className="font-medium">
                      Paso {step.step_number}: {step.titulo}
                    </h3>
                  </div>
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

            {conflictTemplate ? (
              <div className="flex flex-col gap-3 rounded-md border border-warning/30 bg-warning/10 p-4 sm:flex-row sm:items-center sm:justify-between" role="alert">
                <p className="text-sm">
                  La combinación ya está ocupada por <span className="font-medium">{conflictTemplate.nombre}</span> ({conflictTemplate.tipo_orden_nombre || `ID ${conflictTemplate.tipo_orden_id}`} · {conflictTemplate.tipo_unidad_nombre || `ID ${conflictTemplate.tipo_unidad_id}`}).
                </p>
                <AppButton type="button" variant="outline" onClick={() => onShowExistingTemplate(conflictTemplate.id)}>
                  Ver plantilla existente
                </AppButton>
              </div>
            ) : null}

            {isTemplatesLoading ? (
              <p className="text-sm text-muted-foreground" role="status">
                Comprobando combinaciones existentes antes de habilitar la carga…
              </p>
            ) : null}

            {hasTemplatesError ? (
              <p className="rounded-md border border-warning/30 bg-warning/10 p-3 text-sm" role="alert">
                No se pudieron comprobar las plantillas existentes. Puedes continuar; el backend validará la combinación al crearla.
              </p>
            ) : null}

            {isConfirming ? (
              <div className="flex flex-col gap-3 rounded-md border border-primary/30 bg-primary/5 p-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm">La plantilla se creará para esta combinación y no podrá enviarse dos veces.</p>
                <div className="flex shrink-0 gap-2">
                  <AppButton type="button" variant="outline" onClick={() => setIsConfirming(false)} disabled={isSubmitting}>
                    Cancelar
                  </AppButton>
                  <AppButton type="button" onClick={handleUpload} disabled={isSubmitting || isUploadBlocked}>
                    {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {isSubmitting ? "Cargando plantilla..." : "Confirmar carga"}
                  </AppButton>
                </div>
              </div>
            ) : (
              <AppButton type="button" onClick={() => setIsConfirming(true)} disabled={isSubmitting || isUploadBlocked}>
                <Upload className="h-4 w-4" />
                Cargar plantilla
              </AppButton>
            )}
          </AppCardContent>
        </AppCard>
      ) : null}

      {createTemplate.isError ? (
        <ErrorState
          title="No se pudo crear la plantilla"
          description={getUploadErrorMessage(createTemplate.error, conflictTemplate)}
          onRetry={
            template
              ? () => {
                  createTemplate.reset();
                  setIsConfirming(true);
                }
              : undefined
          }
        />
      ) : null}
    </div>
  );
}
