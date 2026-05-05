import { useQuery } from "@tanstack/react-query";
import {
  getClientUnitDetail,
  getClientUnits
} from "@/services/client/units.service";
import type { ClientUnitsParams } from "@/types/client-portal";

export function useClientUnits(params: ClientUnitsParams) {
  return useQuery({
    queryKey: ["client", "units", params],
    queryFn: () => getClientUnits(params)
  });
}

export function useClientUnitDetail(unitId: string) {
  return useQuery({
    queryKey: ["client", "units", unitId],
    queryFn: () => getClientUnitDetail(unitId),
    enabled: Boolean(unitId)
  });
}
