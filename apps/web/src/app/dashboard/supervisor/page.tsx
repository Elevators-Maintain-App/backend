import { RoleDashboardPage } from "@/app/dashboard/_components/role-dashboard-page";

export default function SupervisorDashboardPage() {
  return (
    <RoleDashboardPage
      role="supervisor"
      roleLabel="Supervisor"
      title="Dashboard de supervisor"
      description="Vista placeholder para validar la experiencia inicial del rol supervisor."
    />
  );
}
