import { RoleDashboardPage } from "@/app/dashboard/_components/role-dashboard-page";

export default function AdminDashboardPage() {
  return (
    <RoleDashboardPage
      role="admin"
      roleLabel="Admin"
      title="Dashboard de administracion"
      description="Vista placeholder para validar el acceso administrativo antes de conectar modulos reales."
    />
  );
}
