import { useQuery } from "@tanstack/react-query";
import { getClientDashboard } from "@/services/client/dashboard.service";

export function useClientDashboard() {
  return useQuery({
    queryKey: ["client", "dashboard"],
    queryFn: getClientDashboard
  });
}
