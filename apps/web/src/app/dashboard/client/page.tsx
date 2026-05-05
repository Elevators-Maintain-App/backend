import { RoleDashboardPage } from "@/app/dashboard/_components/role-dashboard-page";

export default function ClientDashboardPage() {
  return (
    <RoleDashboardPage
      role="client"
      roleLabel="Client"
      title="Dashboard de cliente"
      description="Vista placeholder para validar el acceso web de clientes y su ruta protegida."
    />
  );
}
