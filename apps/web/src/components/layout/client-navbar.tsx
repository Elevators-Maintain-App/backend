"use client";

import {
  AlertTriangle,
  ClipboardList,
  LayoutGrid,
  Package,
} from "lucide-react";
import type { DashboardNavItem } from "@/components/layout/dashboard-nav-item";

export const clientNavItems: DashboardNavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard/client",
    icon: LayoutGrid,
    match: "exact",
  },
  {
    label: "Unidades",
    href: "/dashboard/client/units",
    icon: Package,
    match: "prefix",
  },
  {
    label: "Observaciones",
    href: "/dashboard/client/orders",
    icon: ClipboardList,
    match: "prefix",
    excludedQuery: {
      status: "Pendiente",
    },
  },
  {
    label: "Emergencia",
    href: "/dashboard/client/orders?status=Pendiente",
    icon: AlertTriangle,
    match: "exact",
    activeQuery: {
      status: "Pendiente",
    },
  },
];
