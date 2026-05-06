"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { ClientNavbar } from "@/components/layout/client-navbar";
import { useAuth } from "@/hooks/use-auth";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { signOut, userProfile } = useAuth();

  const handleLogout = async () => {
    await signOut();
    router.replace("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      {userProfile?.role === "client" ? (
        <ClientNavbar />
      ) : (
        <header className="border-b bg-card">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-6">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md border bg-background p-1">
                <Image
                  src="/logo.png"
                  alt="VertiOne"
                  width={28}
                  height={28}
                  className="h-7 w-7 object-contain"
                  priority
                />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold">VertiOne</p>
                <p className="truncate text-xs text-muted-foreground">
                  {userProfile?.email || "Web Console"}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                void handleLogout();
              }}
              className="inline-flex h-9 items-center justify-center rounded-md border border-input bg-background px-3 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Cerrar sesion
            </button>
          </div>
        </header>
      )}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
