"use client";

import { useMemo, useState, type ReactNode } from "react";
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from "lucide-react";
import clsx from "clsx";
import { Button } from "@/components/common/ui";

export interface Column<T> {
  key: string;
  header: ReactNode;
  align?: "left" | "right" | "center";
  width?: string;
  sortable?: boolean;
  render: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  emptyMessage?: string;
  pageSize?: number;
  /** Server-side pagination metadata; when absent the table paginates locally. */
  meta?: { page: number; page_size: number; total: number; total_pages: number };
  onPageChange?: (page: number) => void;
  onSort?: (key: string, dir: "asc" | "desc") => void;
  activeSort?: { key: string; dir: "asc" | "desc" } | null;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "No records found.",
  pageSize = 25,
  meta,
  onPageChange,
  onSort,
  activeSort,
}: DataTableProps<T>) {
  const [localSort, setLocalSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);
  const [localPage, setLocalPage] = useState(1);

  const sortedRows = useMemo(() => {
    if (!localSort) return rows;
    const column = columns.find((c) => c.key === localSort.key);
    if (!column?.sortValue) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const va = column.sortValue!(a);
      const vb = column.sortValue!(b);
      const cmp = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
      return localSort.dir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, localSort, columns]);

  const isServerPaginated = Boolean(meta && onPageChange);
  const page = isServerPaginated ? meta!.page : localPage;
  const pageSizeResolved = isServerPaginated ? meta!.page_size : pageSize;
  const total = isServerPaginated ? meta!.total : sortedRows.length;
  const totalPages = isServerPaginated ? meta!.total_pages : Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const visibleRows = isServerPaginated
    ? sortedRows
    : sortedRows.slice((localPage - 1) * pageSizeResolved, localPage * pageSizeResolved);

  const handleSort = (key: string) => {
    const current = activeSort ?? localSort;
    const dir = current?.key === key && current.dir === "desc" ? "asc" : "desc";
    if (onSort) onSort(key, dir);
    else setLocalSort({ key, dir });
  };

  return (
    <div>
      <div className="max-h-[65vh] overflow-auto rounded-b-xl">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  style={column.width ? { width: column.width } : undefined}
                  className={clsx(
                    "border-b border-slate-200 px-4 py-2.5 text-xs font-semibold text-slate-600",
                    column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left",
                  )}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      onClick={() => handleSort(column.key)}
                      className="inline-flex items-center gap-1 hover:text-ink"
                      aria-label={`Sort by ${typeof column.header === "string" ? column.header : column.key}`}
                    >
                      {column.header}
                      {(activeSort ?? localSort)?.key === column.key ? (
                        (activeSort ?? localSort)!.dir === "asc" ? (
                          <ChevronUp size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )
                      ) : null}
                    </button>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-sm text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              visibleRows.map((row) => (
                <tr key={rowKey(row)} className="border-b border-slate-100 transition-colors hover:bg-slate-50/70">
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={clsx(
                        "px-4 py-2.5 align-middle",
                        column.align === "right" ? "text-right" : column.align === "center" ? "text-center" : "text-left",
                      )}
                    >
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-slate-100 px-4 py-2.5 text-xs text-slate-500">
        <span>
          {total === 0 ? "0" : `${(page - 1) * pageSizeResolved + 1}–${Math.min(page * pageSizeResolved, total)}`} of {total}
        </span>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => (onPageChange ? onPageChange(page - 1) : setLocalPage(page - 1))} aria-label="Previous page">
            <ChevronLeft size={14} />
          </Button>
          <span>
            Page {page} / {totalPages}
          </span>
          <Button variant="ghost" size="sm" disabled={page >= totalPages} onClick={() => (onPageChange ? onPageChange(page + 1) : setLocalPage(page + 1))} aria-label="Next page">
            <ChevronRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}
