"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import type { ReadonlyURLSearchParams } from "next/navigation";
import {
  DashboardNavItemLink,
  isDashboardNavItemActive,
  type DashboardNavItem,
} from "@/components/layout/dashboard-nav-item";
import { ProfileDropdown } from "@/components/layout/profile-dropdown";
import { cn } from "@/lib/utils";
import type { UserProfile } from "@/types/auth";

type DashboardSidebarProps = {
  navItems: DashboardNavItem[];
  pathname: string;
  searchParams: ReadonlyURLSearchParams;
  isCollapsed: boolean;
  onToggle: () => void;
  userProfile: UserProfile | null;
  onSignOut: () => Promise<void>;
};

export function DashboardSidebar({
  navItems,
  pathname,
  searchParams,
  isCollapsed,
  onToggle,
  userProfile,
  onSignOut,
}: DashboardSidebarProps) {
  return (
    <aside
      className={cn(
        "hidden h-screen shrink-0 border-r border-border/70 bg-background/95 lg:sticky lg:top-0 lg:flex lg:flex-col",
        "transition-[width] duration-200 ease-out",
        isCollapsed ? "lg:w-20" : "lg:w-64"
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-label={isCollapsed ? "Expandir sidebar" : "Colapsar sidebar"}
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground",
          isCollapsed ? "mx-auto" : "ml-auto"
        )}
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </button>
      <div
        className={cn(
          "flex h-20 items-center justify-center border-b border-border/60 px-4"
        )}
      >
        <Link
          href="/dashboard/client"
          className="flex items-center justify-center"
          aria-label="Ir al dashboard de cliente"
        >
          <Image
            src="/logo.png"
            alt="VertiOne"
            width={140}
            height={42}
            className={cn(
              "h-auto object-contain transition-all duration-200",
              isCollapsed ? "w-10" : "w-28"
            )}
            priority
          />
        </Link>
      </div>

      <div className="flex flex-1 flex-col px-3 py-5">
        <nav className="space-y-1.5">
          {navItems.map((item) => (
            <DashboardNavItemLink
              key={item.label}
              item={item}
              isCollapsed={isCollapsed}
              isActive={isDashboardNavItemActive(item, pathname, searchParams)}
            />
          ))}
        </nav>

        <div className="mt-auto space-y-2 pt-6">
          <div className="rounded-2xl border border-border/70 bg-card/90 p-2 shadow-sm">
            <ProfileDropdown
              userProfile={userProfile}
              onSignOut={onSignOut}
              compact={isCollapsed}
              triggerClassName={cn(
                "w-full rounded-xl",
                isCollapsed
                  ? "justify-center px-1 py-2"
                  : "min-w-0 justify-start px-2.5 py-2.5"
              )}
              menuClassName={cn(
                "w-full",
                isCollapsed
                  ? "bottom-0 left-full right-auto top-auto ml-2 w-64"
                  : "bottom-full left-0 right-auto top-auto mb-2"
              )}
            />
          </div>

        </div>
      </div>
    </aside>
  );
}
