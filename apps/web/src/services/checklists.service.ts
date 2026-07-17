import { apiClient } from "@/lib/api-client";
import type {
  ChecklistTemplateAdmin,
  ChecklistTemplateCreateResponse,
  ChecklistTemplatePayload,
} from "@/types/checklists";

export async function listChecklistTemplates() {
  const response = await apiClient.get<ChecklistTemplateAdmin[]>(
    "/api/checklists/templates"
  );
  return response.data;
}

export async function createChecklistTemplate(payload: ChecklistTemplatePayload) {
  const response = await apiClient.post<ChecklistTemplateCreateResponse>(
    "/api/checklists/templates",
    payload
  );
  return response.data;
}
