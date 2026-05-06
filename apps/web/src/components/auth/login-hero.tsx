import Image from "next/image";

const metrics = [
  { value: "200+", label: "Empresas activas" },
  { value: "50K+", label: "Reportes generados" },
  { value: "99.9%", label: "Disponibilidad" }
];

export function LoginHero() {
  return (
    <section className="relative hidden min-h-[620px] overflow-hidden rounded-[2rem] border border-border/70 bg-card shadow-2xl shadow-emerald-100/60 lg:block">
      <div
        className="absolute inset-0 bg-cover bg-center opacity-25"
        style={{ backgroundImage: "url('/elevator-hero.jpg')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-br from-white via-white/90 to-emerald-50/70" />
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="pointer-events-none absolute -left-24 bottom-12 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl" />

      <div className="relative z-10 flex h-full flex-col justify-between p-12 xl:p-14">
        <div className="space-y-3">
          <Image
            src="/logo.png"
            alt="VertiOne"
            width={118}
            height={54}
            priority
            className="h-auto w-[118px]"
          />
          <p className="text-sm font-semibold text-muted-foreground">Plataforma Web</p>
        </div>

        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
            <span className="text-sm font-medium text-primary">
              Plataforma lider en gestion de mantenimiento
            </span>
          </div>

          <div className="space-y-5">
            <h1 className="max-w-2xl text-5xl font-bold leading-[0.95] tracking-tight text-foreground xl:text-6xl">
              Digitaliza tu{" "}
              <span className="bg-gradient-to-r from-primary via-emerald-500 to-blue-500 bg-clip-text text-transparent">
                operacion de mantenimiento
              </span>
            </h1>

            <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
              Monitoreo en tiempo real, reportes automatizados y trazabilidad completa para equipos de transporte vertical.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-8 border-t border-border/70 pt-8">
          {metrics.map((metric) => (
            <div key={metric.label}>
              <p className="text-3xl font-bold text-foreground">{metric.value}</p>
              <p className="text-sm text-muted-foreground">{metric.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
