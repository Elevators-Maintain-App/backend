import { RoleDashboardPage } from "@/app/dashboard/_components/role-dashboard-page";

export default function SuperAdminDashboardPage() {
  return (
    <RoleDashboardPage
      role="superadmin"
      roleLabel="Super Admin"
      title="Dashboard de super admin"
      description="Vista placeholder para validar la ruta protegida del rol con mayor alcance."
    />
  );
}
