"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Image from "next/image";
import { ArrowRight, Eye, EyeOff, Loader2, Lock, Mail } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { LoginHero } from "@/components/auth/login-hero";
import {
  AppCard,
  AppCardContent,
  AppCardDescription,
  AppCardHeader,
  AppCardTitle
} from "@/components/ui/app-card";
import { AppButton } from "@/components/ui/app-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { getDashboardRouteForRole } from "@/lib/roles";

const loginSchema = z.object({
  email: z.string().email("Ingresa un correo valido."),
  password: z.string().min(6, "La contrasena debe tener al menos 6 caracteres.")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signIn } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting }
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      const profile = await signIn(values.email, values.password);
      const nextPath = searchParams.get("next");

      if (nextPath) {
        router.replace(nextPath);
        return;
      }

      if (profile?.role) {
        router.replace(getDashboardRouteForRole(profile.role));
        return;
      }

      router.replace("/dashboard");
    } catch {
      setError("root", {
        message: "No pudimos iniciar sesion con esas credenciales."
      });
    }
  };

  return (
    <main className="min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-primary/5 via-info/5 to-transparent" />
      <div className="mx-auto grid min-h-screen max-w-7xl items-center gap-8 px-6 py-8 lg:grid-cols-[1.15fr_0.85fr] xl:gap-12">
        <section className="hidden lg:block">
          <LoginHero />
        </section>

        <section className="mx-auto flex w-full max-w-[min(100%,28rem)] flex-col items-center justify-center lg:max-w-md">
          <div className="flex w-full flex-col items-center gap-6 lg:hidden">
            <Image
              src="/logo.png"
              alt="VertiOne"
              width={120}
              height={56}
              priority
              className="mb-2 h-auto w-[120px]"
            />
          </div>

          <AppCard className="w-full max-w-md rounded-[1.75rem] border border-border/80 bg-card p-8 shadow-2xl shadow-emerald-100/50 md:p-10">
            <AppCardHeader className="space-y-2 p-0 pb-6">
              <AppCardTitle className="text-2xl sm:text-[1.8rem]">Iniciar sesion</AppCardTitle>
              <AppCardDescription>
                Usa tus credenciales autorizadas para acceder a la plataforma.
              </AppCardDescription>
            </AppCardHeader>

            <AppCardContent className="p-0">
              <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
                <div className="space-y-2">
                  <Label htmlFor="email">Correo</Label>
                  <div className="relative">
                    <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="nombre@empresa.com"
                      aria-invalid={Boolean(errors.email)}
                      className="h-12 rounded-xl pl-10 pr-4 focus-visible:ring-primary"
                      {...register("email")}
                    />
                  </div>
                  {errors.email?.message ? (
                    <p className="text-sm text-destructive">{errors.email.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Contrasena</Label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      aria-invalid={Boolean(errors.password)}
                      className="h-12 rounded-xl pl-10 pr-11 focus-visible:ring-primary"
                      {...register("password")}
                    />
                    <button
                      type="button"
                      aria-label={showPassword ? "Ocultar contrasena" : "Mostrar contrasena"}
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.password?.message ? (
                    <p className="text-sm text-destructive">{errors.password.message}</p>
                  ) : null}
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-muted-foreground">
                    <input type="checkbox" className="h-4 w-4 rounded border-border" />
                    Mantener sesion iniciada
                  </label>
                  <a href="#" className="text-sm font-medium text-primary hover:underline">
                    Olvidaste tu contrasena?
                  </a>
                </div>

                {errors.root ? (
                  <p className="text-sm text-destructive">{errors.root.message}</p>
                ) : null}

                <AppButton
                  className="h-[52px] w-full rounded-xl shadow-sm"
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  Entrar
                  {!isSubmitting ? <ArrowRight className="h-4 w-4" /> : null}
                </AppButton>

                <p className="text-center text-sm text-muted-foreground">
                  Necesitas acceso?{" "}
                  <a href="#" className="font-medium text-primary hover:underline">
                    Solicita una demo
                  </a>
                </p>
              </form>
            </AppCardContent>
          </AppCard>
        </section>
      </div>
    </main>
  );
}
