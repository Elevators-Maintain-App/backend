"use client";

import { ClipboardList, LayoutGrid } from "lucide-react";
import type { DashboardNavItem } from "@/components/layout/dashboard-nav-item";

export const adminNavItems: DashboardNavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard/admin",
    icon: LayoutGrid,
    match: "exact",
  },
  {
    label: "Checklists",
    href: "/dashboard/admin/checklists",
    icon: ClipboardList,
    match: "prefix",
  },
];
