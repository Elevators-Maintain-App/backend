"use client";

import { Loader2, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useAuth } from "@/hooks/use-auth";
import { getDashboardRouteForRole } from "@/lib/roles";

export default function DashboardPage() {
  const router = useRouter();
  const { firebaseUser, loading, signOut, userProfile, profileError } = useAuth();

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!firebaseUser) {
      router.replace("/login");
      return;
    }

    if (userProfile?.role) {
      router.replace(getDashboardRouteForRole(userProfile.role));
    }
  }, [firebaseUser, loading, router, userProfile?.role]);

  const handleLogout = async () => {
    await signOut();
    router.replace("/login");
  };

  if (loading || (firebaseUser && userProfile?.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <AppCard className="w-full max-w-md">
        <AppCardHeader>
          <p className="text-sm font-medium text-primary">Acceso restringido</p>
          <AppCardTitle>
            {profileError ? "Acceso denegado" : "Rol sin ruta asignada"}
          </AppCardTitle>
        </AppCardHeader>
        <AppCardContent className="space-y-4">
          <p className="text-sm leading-6 text-muted-foreground">
            {profileError ||
              "No existe un dashboard asignado para este usuario todavia."}
          </p>
          <p className="text-sm text-foreground">
            Rol detectado:{" "}
            <span className="font-medium">{userProfile?.rawRole || "sin rol"}</span>
          </p>
          <p className="text-sm text-foreground">
            Rol normalizado:{" "}
            <span className="font-medium">{userProfile?.role || "sin rol"}</span>
          </p>
          <AppButton className="w-full" variant="outline" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Cerrar sesion
          </AppButton>
        </AppCardContent>
      </AppCard>
    </div>
  );
}
