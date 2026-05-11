"use client";

import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReadonlyURLSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

export type DashboardNavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  match?: "exact" | "prefix";
  activeQuery?: Record<string, string>;
  excludedQuery?: Record<string, string>;
};

function matchesQuery(
  searchParams: ReadonlyURLSearchParams,
  query?: Record<string, string>
) {
  if (!query) {
    return true;
  }

  return Object.entries(query).every(
    ([key, value]) => searchParams.get(key) === value
  );
}

export function isDashboardNavItemActive(
  item: DashboardNavItem,
  pathname: string,
  searchParams: ReadonlyURLSearchParams
) {
  const hrefPath = item.href.split("?")[0];
  const isPrefixMatch =
    pathname === hrefPath || pathname.startsWith(`${hrefPath}/`);
  const pathMatches =
    item.match === "prefix" ? isPrefixMatch : pathname === hrefPath;

  if (!pathMatches) {
    return false;
  }

  if (item.activeQuery && !matchesQuery(searchParams, item.activeQuery)) {
    return false;
  }

  if (item.excludedQuery && matchesQuery(searchParams, item.excludedQuery)) {
    return false;
  }

  return true;
}

type DashboardNavItemLinkProps = {
  item: DashboardNavItem;
  isActive: boolean;
  isCollapsed?: boolean;
  onNavigate?: () => void;
};

export function DashboardNavItemLink({
  item,
  isActive,
  isCollapsed = false,
  onNavigate,
}: DashboardNavItemLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      title={isCollapsed ? item.label : undefined}
      onClick={onNavigate}
      className={cn(
        "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary/10 text-primary shadow-sm shadow-emerald-100/60"
          : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
        isCollapsed && "justify-center px-2"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {!isCollapsed ? <span className="truncate">{item.label}</span> : null}
    </Link>
  );
}
