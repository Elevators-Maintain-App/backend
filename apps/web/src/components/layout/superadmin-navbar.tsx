"use client";

import {
  Building2,
  CreditCard,
  FolderKanban,
  LayoutGrid,
  Users,
} from "lucide-react";
import type { DashboardNavItem } from "@/components/layout/dashboard-nav-item";

export const superAdminNavItems: DashboardNavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard/superadmin",
    icon: LayoutGrid,
    match: "exact",
  },
  {
    label: "Compañías",
    href: "/dashboard/superadmin/companies",
    icon: Building2,
    match: "prefix",
  },
  {
    label: "Proyectos",
    href: "/dashboard/superadmin/projects",
    icon: FolderKanban,
    match: "prefix",
  },
  {
    label: "Usuarios",
    href: "/dashboard/superadmin/users",
    icon: Users,
    match: "prefix",
  },
  {
    label: "Planes",
    href: "/dashboard/superadmin/plans",
    icon: CreditCard,
    match: "prefix",
  },
];
