"use client";

import { Menu } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { clientNavItems } from "@/components/layout/client-navbar";
import type { DashboardNavItem } from "@/components/layout/dashboard-nav-item";
import { DashboardSidebar } from "@/components/layout/dashboard-sidebar";
import { MobileDashboardMenu } from "@/components/layout/mobile-dashboard-menu";
import { useAuth } from "@/hooks/use-auth";

const sidebarStorageKey = "vertione:web:client-sidebar-collapsed";

type DashboardShellProps = {
  children: React.ReactNode;
  navItems?: DashboardNavItem[];
  homeHref?: string;
  sidebarStateKey?: string;
};

export function DashboardShell({
  children,
  navItems = clientNavItems,
  homeHref = "/dashboard/client",
  sidebarStateKey = sidebarStorageKey,
}: DashboardShellProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { signOut, userProfile } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [hasLoadedSidebarState, setHasLoadedSidebarState] = useState(false);

  useEffect(() => {
    const storedValue = window.localStorage.getItem(sidebarStateKey);
    setIsCollapsed(storedValue === "true");
    setHasLoadedSidebarState(true);
  }, [sidebarStateKey]);

  useEffect(() => {
    if (!hasLoadedSidebarState) {
      return;
    }

    window.localStorage.setItem(sidebarStateKey, String(isCollapsed));
  }, [hasLoadedSidebarState, isCollapsed, sidebarStateKey]);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname, searchParams]);

  const handleLogout = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen overflow-x-hidden bg-muted/20">
      <div className="lg:flex">
        <DashboardSidebar
          navItems={navItems}
          homeHref={homeHref}
          pathname={pathname}
          searchParams={searchParams}
          isCollapsed={isCollapsed}
          onToggle={() => setIsCollapsed((current) => !current)}
          userProfile={userProfile}
          onSignOut={handleLogout}
        />

        <div className="min-w-0 flex-1">
          <header className="sticky top-0 z-40 border-b border-border/70 bg-background/95 backdrop-blur lg:hidden">
            <div className="relative flex h-16 items-center justify-between px-4 sm:px-6">
              <button
                type="button"
                aria-label="Abrir menu de navegacion"
                aria-expanded={isMobileMenuOpen}
                onClick={() => setIsMobileMenuOpen(true)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted/60 hover:text-foreground"
              >
                <Menu className="h-5 w-5" />
              </button>

              <Link
                href={homeHref}
                className="absolute left-1/2 -translate-x-1/2"
                aria-label="Ir al dashboard"
              >
                <Image
                  src="/logo.png"
                  alt="VertiOne"
                  width={88}
                  height={26}
                  className="h-auto w-20 object-contain sm:w-24"
                  priority
                />
              </Link>

              <div className="h-10 w-10" aria-hidden="true" />
            </div>
          </header>

          <MobileDashboardMenu
            navItems={navItems}
            homeHref={homeHref}
            pathname={pathname}
            searchParams={searchParams}
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
            userProfile={userProfile}
            onSignOut={handleLogout}
          />

          <main className="min-w-0">
            <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
