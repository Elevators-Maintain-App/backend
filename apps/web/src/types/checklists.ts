import { z } from "zod";

const jsonValueSchema: z.ZodType<unknown> = z.lazy(() =>
  z.union([
    z.string(),
    z.number(),
    z.boolean(),
    z.null(),
    z.array(jsonValueSchema),
    z.record(jsonValueSchema),
  ])
);

const evidenceSchema = z.record(jsonValueSchema);

export const checklistTemplateSchema = z.object({
  nombre: z.string().trim().min(1, "El nombre de la plantilla es obligatorio."),
  tipo_orden_id: z.number().int("El tipo de orden debe ser un número entero."),
  tipo_unidad_id: z.number().int("El tipo de unidad debe ser un número entero."),
  pasos: z
    .array(
      z.object({
        step_number: z
          .number()
          .int("El número de paso debe ser un número entero.")
          .positive("El número de paso debe ser mayor que cero."),
        titulo: z.string().trim().min(1, "Cada paso debe tener un título."),
        instrucciones: z
          .string()
          .trim()
          .min(1, "Cada paso debe tener instrucciones."),
        evidencia_schema: evidenceSchema,
      })
    )
    .min(1, "La plantilla debe incluir al menos un paso."),
});

export type ChecklistTemplatePayload = z.infer<typeof checklistTemplateSchema>;

export type ChecklistTemplateCreateResponse = {
  id: string;
  nombre: string;
  tipo_orden_id: number;
  tipo_unidad_id: number;
  pasos_ids: string[];
};

export type ChecklistTemplateAdminStep = {
  id: string;
  step_number: number;
  titulo: string;
  instrucciones: string;
  evidencia_schema: Record<string, unknown>;
};

export type ChecklistTemplateAdmin = {
  id: string;
  nombre: string;
  tipo_orden_id: number;
  tipo_orden_nombre: string | null;
  tipo_unidad_id: number;
  tipo_unidad_nombre: string | null;
  total_steps: number;
  created_at: string | null;
  updated_at: string | null;
  pasos: ChecklistTemplateAdminStep[];
};
