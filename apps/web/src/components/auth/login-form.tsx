"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppInput } from "@/components/forms/app-input";
import { AppButton } from "@/components/ui/app-button";
import { useAuth } from "@/hooks/use-auth";
import { getDashboardRouteForRole } from "@/lib/roles";

const loginSchema = z.object({
  email: z.string().email("Ingresa un correo valido."),
  password: z.string().min(6, "La contrasena debe tener al menos 6 caracteres.")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginForm() {
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
    <main className="min-h-screen bg-background">
      <div className="mx-auto grid min-h-screen max-w-6xl grid-cols-1 lg:grid-cols-[1fr_420px]">
        <section className="hidden flex-col justify-between border-r bg-muted/50 px-10 py-12 lg:flex">
          <div className="text-sm font-semibold uppercase tracking-wide text-primary">
            VertiOne Web
          </div>
          <div className="max-w-xl">
            <h1 className="text-4xl font-semibold leading-tight">
              Operacion, reportes y control de campo en un solo panel.
            </h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground">
              Acceso web protegido para equipos internos de VertiOne.
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            API permitida: /api/web/*
          </div>
        </section>

        <section className="flex items-center px-6 py-10 sm:px-10">
          <div className="w-full">
            <div className="mb-8 lg:hidden">
              <p className="text-sm font-semibold uppercase tracking-wide text-primary">
                VertiOne Web
              </p>
              <h1 className="mt-3 text-3xl font-semibold">Iniciar sesion</h1>
            </div>
            <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
              <div className="hidden lg:block">
                <h2 className="text-2xl font-semibold">Iniciar sesion</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Usa tus credenciales autorizadas para entrar.
                </p>
              </div>

              <AppInput
                label="Correo"
                type="email"
                autoComplete="email"
                placeholder="nombre@empresa.com"
                error={errors.email?.message}
                {...register("email")}
              />

              <AppInput
                label="Contrasena"
                type="password"
                autoComplete="current-password"
                error={errors.password?.message}
                {...register("password")}
              />

              {errors.root ? (
                <p className="text-sm text-destructive">{errors.root.message}</p>
              ) : null}

              <AppButton className="w-full" type="submit" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Entrar
              </AppButton>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}
