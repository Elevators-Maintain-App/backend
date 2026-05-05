import { useQuery } from "@tanstack/react-query";
import {
  getClientOrderDetail,
  getClientOrderReport,
  getClientOrders
} from "@/services/client/orders.service";
import type { ClientOrdersParams } from "@/types/client-portal";

export function useClientOrders(params: ClientOrdersParams) {
  return useQuery({
    queryKey: ["client", "orders", params],
    queryFn: () => getClientOrders(params)
  });
}

export function useClientOrderDetail(orderId: string) {
  return useQuery({
    queryKey: ["client", "orders", orderId],
    queryFn: () => getClientOrderDetail(orderId),
    enabled: Boolean(orderId)
  });
}

export function useClientOrderReport(orderId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["client", "orders", orderId, "report"],
    queryFn: () => getClientOrderReport(orderId),
    enabled: Boolean(orderId) && enabled
  });
}
