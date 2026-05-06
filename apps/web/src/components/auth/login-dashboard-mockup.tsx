export function LoginDashboardMockup() {
  const bars = [40, 65, 45, 80, 55, 90, 70, 85, 60, 95, 75, 88];

  return (
    <div className="relative pt-4">
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-xl shadow-slate-200/70">
        <div className="flex items-center gap-2 border-b border-border bg-muted/50 px-4 py-3">
          <div className="flex gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-400/70" />
            <span className="h-3 w-3 rounded-full bg-yellow-400/70" />
            <span className="h-3 w-3 rounded-full bg-primary/60" />
          </div>
          <div className="mx-4 flex-1 rounded-lg bg-background/80 px-3 py-1.5 text-center text-xs text-muted-foreground">
            app.verti-one.com/dashboard
          </div>
        </div>

        <div className="space-y-5 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Panel de Control</h3>
              <p className="text-sm text-muted-foreground">Resumen operativo</p>
            </div>

            <div className="flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary">
              <span className="h-2 w-2 rounded-full bg-primary" />
              En vivo
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Trabajos Hoy", value: "24", change: "+12%" },
              { label: "Completados", value: "18", change: "+8%" },
              { label: "Tecnicos Activos", value: "12", change: "" }
            ].map((item) => (
              <div key={item.label} className="rounded-xl bg-muted/30 p-4">
                <p className="mb-1 text-xs text-muted-foreground">{item.label}</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-foreground">{item.value}</span>
                  {item.change ? (
                    <span className="text-xs font-medium text-primary">{item.change}</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl bg-muted/30 p-4">
            <div className="flex h-24 items-end justify-between gap-2">
              {bars.map((height, index) => (
                <div
                  key={index}
                  className="flex-1 rounded-t-sm bg-primary/20"
                  style={{ height: `${height}%` }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="absolute -left-8 top-32 hidden rounded-xl border border-border bg-card p-4 shadow-xl shadow-slate-200/70 md:block">
        <p className="text-sm font-medium text-foreground">Reporte generado</p>
        <p className="text-xs text-muted-foreground">Hace 2 minutos</p>
      </div>

      <div className="absolute -right-6 bottom-20 hidden rounded-xl border border-border bg-card p-4 shadow-xl shadow-slate-200/70 md:block">
        <p className="text-sm font-medium text-foreground">Checklist completado</p>
        <p className="text-xs text-muted-foreground">Tecnico #24</p>
      </div>
    </div>
  );
}
