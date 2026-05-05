import * as React from "react";
import { cn } from "@/lib/utils";

type DataTableColumn<TData> = {
  key: string;
  header: string;
  cell: (row: TData) => React.ReactNode;
  className?: string;
};

type DataTableProps<TData> = {
  columns: DataTableColumn<TData>[];
  data: TData[];
  getRowKey: (row: TData) => string;
};

export function DataTable<TData>({
  columns,
  data,
  getRowKey
}: DataTableProps<TData>) {
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b bg-muted/60 text-xs uppercase text-muted-foreground">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={cn("px-4 py-3", column.className)}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={getRowKey(row)} className="border-b last:border-b-0">
                {columns.map((column) => (
                  <td key={column.key} className={cn("px-4 py-3", column.className)}>
                    {column.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="divide-y md:hidden">
        {data.map((row) => (
          <div key={getRowKey(row)} className="space-y-3 p-4">
            {columns.map((column) => (
              <div key={column.key} className="space-y-1">
                <p className="text-xs font-medium uppercase text-muted-foreground">
                  {column.header}
                </p>
                <div className="text-sm">{column.cell(row)}</div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
