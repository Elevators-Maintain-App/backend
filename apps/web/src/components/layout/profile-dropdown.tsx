"use client";

import { ChevronDown, LogOut, UserRound } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { AppButton } from "@/components/ui/app-button";
import { cn } from "@/lib/utils";
import type { UserProfile } from "@/types/auth";

type ProfileDropdownProps = {
  userProfile: UserProfile | null;
  onSignOut: () => Promise<void>;
  compact?: boolean;
  triggerClassName?: string;
  menuClassName?: string;
};

function getInitials(userProfile: UserProfile | null) {
  const source = userProfile?.displayName || userProfile?.email || "C";
  return source
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("");
}

export function UserAvatar({
  userProfile,
  className,
}: {
  userProfile: UserProfile | null;
  className?: string;
}) {
  if (userProfile?.photoUrl) {
    return (
      <Image
        src={userProfile.photoUrl}
        alt={userProfile.displayName || "Usuario"}
        width={36}
        height={36}
        className={cn("h-9 w-9 shrink-0 rounded-full object-cover", className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary",
        className
      )}
    >
      {getInitials(userProfile)}
    </div>
  );
}

export function ProfileDropdown({
  userProfile,
  onSignOut,
  compact = false,
  triggerClassName,
  menuClassName,
}: ProfileDropdownProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={cn(
          "flex items-center gap-2 rounded-xl px-2 py-2 text-left transition-colors hover:bg-muted/40",
          compact && "justify-center gap-0",
          triggerClassName
        )}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <UserAvatar userProfile={userProfile} />

        {!compact ? (
          <div className="hidden min-w-0 flex-1 sm:block">
            <p className="truncate text-sm font-semibold text-foreground">
              {userProfile?.displayName || "Cliente VertiOne"}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {userProfile?.role === "client"
                ? "Cliente"
                : userProfile?.rawRole || "Usuario"}
            </p>
          </div>
        ) : null}

        {!compact ? (
          <ChevronDown
            className={cn(
              "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
              open ? "rotate-180" : ""
            )}
          />
        ) : null}
      </button>

      {open ? (
        <div
          className={cn(
            "absolute right-0 top-[calc(100%+0.75rem)] z-50 w-[280px] rounded-2xl border border-border/70 bg-card p-2 shadow-[0_10px_30px_rgba(15,23,42,0.10)]",
            menuClassName
          )}
        >
          <div className="rounded-xl bg-muted/35 px-4 py-3">
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

          <div className="my-2 h-px bg-border/80" />

          <div className="space-y-1">
            <AppButton
              variant="ghost"
              className="w-full justify-start rounded-xl px-3"
              onClick={() => setOpen(false)}
            >
              <UserRound className="h-4 w-4" />
              Mi perfil
            </AppButton>

            <AppButton
              variant="ghost"
              className="w-full justify-start rounded-xl px-3 text-destructive hover:bg-destructive/5 hover:text-destructive"
              onClick={() => {
                setOpen(false);
                void onSignOut();
              }}
            >
              <LogOut className="h-4 w-4" />
              Cerrar sesion
            </AppButton>
          </div>
        </div>
      ) : null}
    </div>
  );
}
