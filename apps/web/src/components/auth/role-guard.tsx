"use client";

import { Loader2, LogOut } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppButton } from "@/components/ui/app-button";
import {
  AppCard,
  AppCardContent,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { useAuth } from "@/hooks/use-auth";
import type { NormalizedUserRole } from "@/types/auth";

type RoleGuardProps = {
  allowedRoles: NormalizedUserRole[];
  children: React.ReactNode;
};

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { firebaseUser, userProfile, profileError, loading, signOut } = useAuth();
  const hasAllowedRole =
    userProfile?.role && allowedRoles.includes(userProfile.role);

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!firebaseUser) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
  }, [firebaseUser, loading, pathname, router]);

  if (loading || !firebaseUser) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!hasAllowedRole) {
    const handleLogout = async () => {
      await signOut();
      router.replace("/login");
    };

    const title = profileError ? "Acceso denegado" : "Rol no autorizado";
    const description =
      profileError ||
      "Tu usuario no tiene permisos para esta vista. Solicita a un administrador revisar tu rol en Firestore.";

    return (
      <div className="flex min-h-screen items-center justify-center px-6">
        <AppCard className="w-full max-w-md">
          <AppCardHeader>
            <p className="text-sm font-medium text-primary">Acceso restringido</p>
            <AppCardTitle>{title}</AppCardTitle>
          </AppCardHeader>
          <AppCardContent className="space-y-4">
            <p className="text-sm leading-6 text-muted-foreground">
              {description}
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

  return <>{children}</>;
}
