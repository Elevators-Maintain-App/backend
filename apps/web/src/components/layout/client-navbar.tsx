"use client";

import {
  AlertTriangle,
  ClipboardList,
  LayoutGrid,
  UserRound
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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

  const handleLogout = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col px-4 sm:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-4">
            <Link href="/dashboard/client" className="flex items-center">
              <Image
                src="/logo.png"
                alt="VertiOne"
                width={150}
                height={44}
                className="h-10 w-auto md:h-11"
                priority
              />
            </Link>

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

        <div className="-mx-1 flex gap-2 overflow-x-auto pb-3 lg:hidden">
          {navigationItems.map(({ label, href, icon: Icon, isActive }) => {
            const active = isActivePath(pathname, href, isActive === false);

            return (
              <Link
                key={label}
                href={href}
                className={cn(
                  "inline-flex shrink-0 items-center gap-2 rounded-xl border px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "border-primary/20 bg-primary/10 text-primary"
                    : "border-border/60 bg-card text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
}
