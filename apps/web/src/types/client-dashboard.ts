export type ClientDashboard = {
  client: {
    id: string;
    name: string;
  };
  summary: {
    total_projects: number;
    total_units: number;
    open_orders: number;
    closed_orders: number;
  };
  recent_orders: ClientRecentOrder[];
};

export type ClientRecentOrder = {
  id: string;
  reference: string | null;
  date: string | null;
  status: string;
  unit: string;
  project: string;
};
