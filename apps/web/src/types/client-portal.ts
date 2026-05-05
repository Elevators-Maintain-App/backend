export type ClientPage<TData> = {
  data: TData[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ClientUnit = {
  id: string;
  name: string;
  project_id: string;
  project: string;
  type: string | null;
  kpi_functioning: string | null;
};

export type ClientUnitDetail = ClientUnit & {
  company_id: string;
  client_id: string;
  created_at: string | null;
  updated_at: string | null;
};

export type ClientUnitsParams = {
  page: number;
  page_size: number;
  search?: string;
  project_id?: string;
};

export type ClientOrder = {
  id: string;
  reference: string | null;
  date: string | null;
  status: string;
  project_id: string;
  project: string;
  unit_id: string;
  unit: string;
  type: string | null;
  priority: string | null;
  has_report: boolean;
};

export type ClientOrderDetail = ClientOrder & {
  description: string | null;
  observations: string | null;
  technician: string | null;
  supervisor: string | null;
  final_report_url: string | null;
};

export type ClientOrdersParams = {
  page: number;
  page_size: number;
  search?: string;
  status?: string;
  unit_id?: string;
  project_id?: string;
};

export type ClientReportLink = {
  report_url: string;
};
