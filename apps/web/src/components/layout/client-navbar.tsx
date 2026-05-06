"use client";

import {
  AlertTriangle,
  ClipboardList,
  LayoutGrid,
  Menu,
  UserRound
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { ProfileDropdown } from "@/components/layout/profile-dropdown";
import { cn } from "@/lib/utils";

const navigationItems = [
  {
    label: "Dashboard",
    href: "/dashboard/client",
    icon: LayoutGrid
  },
  {
    label: "Observaciones",
    href: "/dashboard/client/orders",
    icon: ClipboardList
  },
  {
    label: "Emergencia",
    href: "/dashboard/client/orders?status=Pendiente",
    icon: AlertTriangle
  },
  {
    label: "Perfil",
    href: "/dashboard/client",
    isActive: false,
    icon: UserRound
  }
];

function isActivePath(pathname: string, href: string, forceInactive?: boolean) {
  if (forceInactive) {
    return false;
  }
  const hrefPath = href.split("?")[0];
  return pathname === hrefPath;
}

export function ClientNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { signOut, userProfile } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!mobileMenuRef.current?.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const handleLogout = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="relative mx-auto flex max-w-7xl flex-col px-4 sm:px-6" ref={mobileMenuRef}>
        <div className="flex h-16 items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-4 lg:hidden">
            <button
              type="button"
              aria-label="Abrir menu de navegacion"
              aria-expanded={isMenuOpen}
              onClick={() => setIsMenuOpen((value) => !value)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>

          <div className="absolute left-1/2 -translate-x-1/2 lg:static lg:translate-x-0">
            <Link href="/dashboard/client" className="flex items-center">
              <Image
                src="/logo.png"
                alt="VertiOne"
                width={150}
                height={44}
                className="h-9 w-auto lg:h-10 xl:h-11"
                priority
              />
            </Link>
          </div>

          <div className="hidden min-w-0 items-center gap-4 lg:flex">
            <nav className="hidden items-center gap-1 lg:flex">
              {navigationItems.map(({ label, href, icon: Icon, isActive }) => {
                const active = isActivePath(pathname, href, isActive === false);

                return (
                  <Link
                    key={label}
                    href={href}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary/10 text-primary shadow-sm shadow-emerald-100"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-2">
            <ProfileDropdown userProfile={userProfile} onSignOut={handleLogout} />
          </div>
        </div>

        {isMenuOpen ? (
          <div
            role="menu"
            className="absolute left-4 top-[calc(100%+0.75rem)] z-50 w-[280px] rounded-2xl border border-border/70 bg-card p-2 shadow-[0_10px_30px_rgba(15,23,42,0.10)] lg:hidden"
          >
            <div className="space-y-1">
              {navigationItems.map(({ label, href, icon: Icon, isActive }) => {
                const active = isActivePath(pathname, href, isActive === false);

                return (
                  <Link
                    key={label}
                    href={href}
                    role="menuitem"
                    onClick={() => setIsMenuOpen(false)}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary/10 text-primary shadow-sm shadow-emerald-100"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </Link>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
}
