"use client";

import { Building2, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { AppButton } from "@/components/ui/app-button";
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
      <header className="border-b bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-6">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Building2 className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold">VertiOne</p>
              <p className="truncate text-xs text-muted-foreground">
                {userProfile?.email || "Web Console"}
              </p>
            </div>
          </div>
          <AppButton variant="outline" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Cerrar sesion
          </AppButton>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
