"use client";

import { LogOut, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect } from "react";
import type { ReadonlyURLSearchParams } from "next/navigation";
import {
  DashboardNavItemLink,
  isDashboardNavItemActive,
  type DashboardNavItem,
} from "@/components/layout/dashboard-nav-item";
import { AppButton } from "@/components/ui/app-button";
import { cn } from "@/lib/utils";
import type { UserProfile } from "@/types/auth";

function getInitials(userProfile: UserProfile | null) {
  const source = userProfile?.displayName || userProfile?.email || "C";
  return source
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");
}

type MobileDashboardMenuProps = {
  navItems: DashboardNavItem[];
  pathname: string;
  searchParams: ReadonlyURLSearchParams;
  isOpen: boolean;
  onClose: () => void;
  userProfile: UserProfile | null;
  onSignOut: () => Promise<void>;
};

export function MobileDashboardMenu({
  navItems,
  pathname,
  searchParams,
  isOpen,
  onClose,
  userProfile,
  onSignOut,
}: MobileDashboardMenuProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] bg-background lg:hidden">
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-border/70 px-4 py-4 sm:px-6">
          <Link href="/dashboard/client" onClick={onClose} className="flex items-center">
            <Image
              src="/logo.png"
              alt="VertiOne"
              width={118}
              height={34}
              className="h-auto w-24 object-contain sm:w-28"
              priority
            />
          </Link>

          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar menu de navegacion"
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6">
          <nav className="space-y-2">
            {navItems.map((item) => (
              <DashboardNavItemLink
                key={item.label}
                item={item}
                isActive={isDashboardNavItemActive(item, pathname, searchParams)}
                onNavigate={onClose}
              />
            ))}
          </nav>

          <div className="mt-auto rounded-2xl border border-border/70 bg-card p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                {getInitials(userProfile)}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">
                  {userProfile?.displayName || "Cliente VertiOne"}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {userProfile?.email || "Correo no disponible"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {userProfile?.role === "client"
                    ? "Portal cliente"
                    : userProfile?.rawRole || "VertiOne Web"}
                </p>
              </div>
            </div>

            <AppButton
              variant="ghost"
              className={cn(
                "mt-4 w-full justify-start rounded-xl px-3 text-destructive",
                "hover:bg-destructive/5 hover:text-destructive"
              )}
              onClick={() => {
                onClose();
                void onSignOut();
              }}
            >
              <LogOut className="h-4 w-4" />
              Cerrar sesion
            </AppButton>
          </div>
        </div>
      </div>
    </div>
  );
}
