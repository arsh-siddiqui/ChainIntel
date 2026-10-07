"use client";

import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton } from "@/components/common/ui";
import { DataTable, type Column } from "@/components/common/data-table";
import { Modal } from "@/components/common/modal";
import { CopyButton } from "@/components/common/copy-button";
import { formatCrypto, formatDateTime, truncateMiddle } from "@/lib/formatters";
import type { NormalizedTx, PageMeta } from "@/types";

function TransactionsInner() {
  const searchParams = useSearchParams();
  const [filters, setFilters] = useState({
    search: searchParams.get("search") ?? "",
    blockchain: "",
    min_amount: "",
    max_amount: "",
    start: "",
    end: "",
  });
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" }>({ key: "timestamp", dir: "desc" });
  const [selected, setSelected] = useState<NormalizedTx | null>(null);
  const [appliedSearch, setAppliedSearch] = useState(searchParams.get("search") ?? "");

  const queryString = useMemo(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "25", sort_by: sort.key, sort_dir: sort.dir });
    if (appliedSearch) params.set("search", appliedSearch);
    if (filters.blockchain) params.set("blockchain", filters.blockchain);
    if (filters.min_amount) params.set("min_amount", filters.min_amount);
    if (filters.max_amount) params.set("max_amount", filters.max_amount);
    if (filters.start) params.set("start", filters.start);
    if (filters.end) params.set("end", filters.end);
    return params.toString();
  }, [page, sort, appliedSearch, filters]);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["transactions", queryString],
    queryFn: async () => {
      const response = await api.get<NormalizedTx[]>(`/transactions?${queryString}`);
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
  });

  const columns: Column<NormalizedTx>[] = [
    {
      key: "tx_hash",
      header: "TX Hash",
      sortable: true,
      render: (tx) => (
        <button type="button" onClick={() => setSelected(tx)} className="font-mono text-xs font-medium text-primary hover:underline">
          {truncateMiddle(tx.tx_hash, 16, 8)}
        </button>
      ),
    },
    { key: "blockchain", header: "Chain", render: (tx) => <span className="text-xs capitalize text-slate-600">{tx.blockchain}</span> },
    { key: "from", header: "From", render: (tx) => <span className="font-mono text-[11px] text-slate-600">{truncateMiddle(tx.from_address ?? "—", 10, 6)}</span> },
    { key: "to", header: "To", render: (tx) => <span className="font-mono text-[11px] text-slate-600">{truncateMiddle(tx.to_address ?? "—", 10, 6)}</span> },
    { key: "amount", header: "Amount", align: "right", sortable: true, render: (tx) => <span className="font-mono text-xs font-medium">{formatCrypto(tx.amount, tx.asset)}</span> },
    { key: "timestamp", header: "Timestamp", sortable: true, render: (tx) => <span className="text-xs text-slate-500">{formatDateTime(tx.timestamp)}</span> },
    { key: "confirmations", header: "Conf.", align: "right", render: (tx) => <span className="text-xs text-slate-500">{tx.confirmations.toLocaleString()}</span> },
    { key: "status", header: "Status", render: (tx) => <Badge className={tx.status === "confirmed" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}>{tx.status}</Badge> },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-heading text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">Transaction Explorer & Ledger Audit</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">All normalized transactions in the indexed dataset.</p>
      </div>

      <Card className="p-4">
        <div className="grid gap-2 md:grid-cols-3 lg:grid-cols-6">
          <form
            className="relative md:col-span-2"
            onSubmit={(event) => {
              event.preventDefault();
              setAppliedSearch(filters.search);
              setPage(1);
            }}
          >
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="Search hash / address…" className="pl-8" aria-label="Search transactions" />
          </form>
          <Select value={filters.blockchain} onChange={(e) => { setFilters({ ...filters, blockchain: e.target.value }); setPage(1); }} aria-label="Blockchain filter">
            <option value="">All chains</option>
            <option value="bitcoin">Bitcoin</option>
            <option value="ethereum">Ethereum</option>
            <option value="bsc">BSC</option>
          </Select>
          <Input type="number" step="any" value={filters.min_amount} onChange={(e) => setFilters({ ...filters, min_amount: e.target.value })} placeholder="Min amount" aria-label="Minimum amount" />
          <Input type="number" step="any" value={filters.max_amount} onChange={(e) => setFilters({ ...filters, max_amount: e.target.value })} placeholder="Max amount" aria-label="Maximum amount" />
          <div className="flex gap-2">
            <Input type="date" value={filters.start} onChange={(e) => setFilters({ ...filters, start: e.target.value })} aria-label="Start date" />
            <Input type="date" value={filters.end} onChange={(e) => setFilters({ ...filters, end: e.target.value })} aria-label="End date" />
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Transactions"
          subtitle={data ? `${data.meta.total.toLocaleString()} records` : "Loading…"}
          action={isFetching ? <Spinner /> : undefined}
        />
        {isError ? (
          <p className="px-5 py-8 text-center text-sm text-red-600">{(error as Error).message}</p>
        ) : isLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={data?.rows ?? []}
            rowKey={(tx) => tx.tx_hash}
            meta={data?.meta}
            onPageChange={(p) => setPage(p)}
            onSort={(key, dir) => {
              setSort({ key, dir });
              setPage(1);
            }}
            activeSort={sort}
            emptyMessage="No transactions match the current filters."
          />
        )}
      </Card>

      <Modal open={selected !== null} onClose={() => setSelected(null)} title="Transaction detail" wide>
        {selected ? (
          <div className="space-y-2.5 text-sm">
            {[
              ["TX Hash", selected.tx_hash, true],
              ["Blockchain", selected.blockchain, false],
              ["Block", selected.block_number !== null ? String(selected.block_number) : "—", false],
              ["Timestamp", formatDateTime(selected.timestamp), false],
              ["Sender", selected.from_address ?? "—", true],
              ["Receiver", selected.to_address ?? "—", true],
              ["Amount", formatCrypto(selected.amount, selected.asset), false],
              ["Fee", selected.fee !== null ? formatCrypto(selected.fee, selected.asset) : "—", false],
              ["Confirmations", selected.confirmations.toLocaleString(), false],
              ["Status", selected.status, false],
              ["Data source", "LIVE provider", false],
            ].map(([label, value, copy]) => (
              <div key={label as string} className="flex items-center justify-between gap-3 border-b border-slate-100 pb-2">
                <span className="shrink-0 text-xs font-medium text-slate-500">{label as string}</span>
                <span className="flex min-w-0 items-center gap-1 font-mono text-xs text-ink">
                  <span className="truncate" title={value as string}>{value as string}</span>
                  {copy ? <CopyButton value={value as string} /> : null}
                </span>
              </div>
            ))}
            <div className="pt-1">
              <Button size="sm" variant="secondary" onClick={() => { setSelected(null); void refetch(); }}>
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

export default function TransactionsPage() {
  return (
    <Suspense fallback={<Card className="p-6"><Spinner /> Loading…</Card>}>
      <TransactionsInner />
    </Suspense>
  );
}
