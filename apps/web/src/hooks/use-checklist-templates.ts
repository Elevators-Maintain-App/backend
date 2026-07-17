import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createChecklistTemplate,
  listChecklistTemplates,
} from "@/services/checklists.service";
import type { ChecklistTemplatePayload } from "@/types/checklists";

export const checklistTemplatesQueryKey = ["admin", "checklist-templates"] as const;

export function useChecklistTemplates() {
  return useQuery({
    queryKey: checklistTemplatesQueryKey,
    queryFn: listChecklistTemplates,
  });
}

export function useCreateChecklistTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: ChecklistTemplatePayload) => createChecklistTemplate(payload),
    retry: false,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: checklistTemplatesQueryKey });
    },
    onError: async (error) => {
      if (typeof error === "object" && error !== null && "response" in error) {
        const response = (error as { response?: { status?: number } }).response;
        if (response?.status === 409) {
          await queryClient.invalidateQueries({ queryKey: checklistTemplatesQueryKey });
        }
      }
    },
  });
}
