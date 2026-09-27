"use client";

import { Suspense, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ExternalLink, Upload } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton } from "@/components/common/ui";
import { DataTable, type Column } from "@/components/common/data-table";
import { THREAT_CATEGORIES } from "@/lib/constants";
import { confidencePercent, formatDateTime, titleCase, truncateMiddle } from "@/lib/formatters";
import type { ImportStats, PageMeta, ThreatFinding } from "@/types";

interface ThreatStats {
  total: number;
  flagged_wallets: number;
  categories: { category: string; count: number }[];
  sources: { source: string; count: number }[];
}

const CATEGORY_BADGE: Record<string, string> = {
  Ransomware: "bg-red-50 text-red-700 border-red-200",
  Scam: "bg-orange-50 text-orange-700 border-orange-200",
  Phishing: "bg-amber-50 text-amber-700 border-amber-200",
  Blacklist: "bg-red-50 text-red-700 border-red-200",
  Fraud: "bg-orange-50 text-orange-700 border-orange-200",
  Exploit: "bg-red-50 text-red-700 border-red-200",
  "Suspicious Service": "bg-purple-50 text-purple-700 border-purple-200",
  Unknown: "bg-slate-100 text-slate-600 border-slate-200",
};

function ThreatsInner() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [filters, setFilters] = useState({ search: searchParams.get("search") ?? "", category: "" });
  const [applied, setApplied] = useState({ search: searchParams.get("search") ?? "", category: "" });
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["threats", applied, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (applied.search) params.set("search", applied.search);
      if (applied.category) params.set("category", applied.category);
      const response = await api.get<ThreatFinding[]>(`/threats?${params.toString()}`);
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
  });

  const { data: stats } = useQuery({
    queryKey: ["threat-stats"],
    queryFn: async () => (await api.get<ThreatStats>("/threats/stats")).data,
  });

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return (await api.upload<ImportStats>("/threats/import", form)).data;
    },
    onSuccess: (statsResult) => {
      toast.success(`Import complete: ${statsResult.inserted} inserted, ${statsResult.updated} updated, ${statsResult.invalid} invalid`);
      void queryClient.invalidateQueries({ queryKey: ["threats"] });
      void queryClient.invalidateQueries({ queryKey: ["threat-stats"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Import failed"),
  });

  const columns: Column<ThreatFinding>[] = [
    { key: "wallet", header: "Wallet", render: (t) => <span className="font-mono text-xs text-ink">{truncateMiddle(t.wallet_address, 16, 8)}</span> },
    { key: "category", header: "Threat Type", render: (t) => <Badge className={CATEGORY_BADGE[t.category] ?? CATEGORY_BADGE.Unknown}>{t.category}</Badge> },
    { key: "label", header: "Group / Label", render: (t) => <span className="text-xs text-slate-700">{t.label}</span> },
    { key: "source", header: "Source", render: (t) => <span className="text-[11px] text-slate-500">{t.source}</span> },
    { key: "confidence", header: "Confidence", align: "right", render: (t) => <span className="text-xs font-medium text-purple-700">{confidencePercent(t.confidence)}</span> },
    { key: "first_seen", header: "First Seen", render: (t) => <span className="text-xs text-slate-500">{formatDateTime(t.first_seen)}</span> },
    { key: "last_seen", header: "Last Seen", render: (t) => <span className="text-xs text-slate-500">{formatDateTime(t.last_seen)}</span> },
    {
      key: "evidence",
      header: "Evidence",
      render: (t) =>
        t.reference_url ? (
          <a href={t.reference_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
            <ExternalLink size={11} /> Reference
          </a>
        ) : (
          <span className="text-[11px] text-slate-400">—</span>
        ),
    },
    { key: "data", header: "Data", render: () => <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Imported</Badge> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">Threat Intelligence</h2>
          <p className="text-xs text-slate-500">Configured threat datasets. Every record carries its source and evidence reference.</p>
        </div>
        <div className="flex items-center gap-2">
          {stats ? (
            <>
              <Badge className="bg-purple-50 text-purple-700 border-purple-200">{stats.total} records</Badge>
              <Badge className="bg-red-50 text-red-700 border-red-200">{stats.flagged_wallets} flagged wallets</Badge>
            </>
          ) : (
            <Skeleton className="h-5 w-40" />
          )}
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {(stats?.categories ?? []).slice(0, 8).map((entry) => (
          <Card key={entry.category} className="flex items-center justify-between px-4 py-3">
            <Badge className={CATEGORY_BADGE[entry.category] ?? CATEGORY_BADGE.Unknown}>{entry.category}</Badge>
            <span className="text-lg font-semibold text-ink">{entry.count}</span>
          </Card>
        ))}
      </div>

      <Card className="p-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <form
            className="md:flex-1"
            onSubmit={(event) => {
              event.preventDefault();
              setApplied(filters);
              setPage(1);
            }}
          >
            <Input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="Search address, label or source…" aria-label="Search threats" />
          </form>
          <Select
            value={filters.category}
            onChange={(e) => {
              setFilters({ ...filters, category: e.target.value });
              setApplied({ ...filters, category: e.target.value });
              setPage(1);
            }}
            aria-label="Category filter"
            className="md:w-52"
          >
            <option value="">All categories</option>
            {THREAT_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </Select>
          <div className="flex items-center gap-2">
            <input ref={fileRef} type="file" accept=".csv,.json" className="hidden" onChange={(e) => { const file = e.target.files?.[0]; if (file) importMutation.mutate(file); e.target.value = ""; }} aria-label="Upload threat dataset" />
            <Button variant="secondary" onClick={() => fileRef.current?.click()} disabled={importMutation.isPending}>
              {importMutation.isPending ? <Spinner /> : <Upload size={14} />} Import CSV/JSON
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Threat database" subtitle="Filter by category, search by address / label / source" />
        {isLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={data?.rows ?? []}
            rowKey={(t, ) => `${t.wallet_address}-${t.source}-${t.label}`}
            meta={data?.meta}
            onPageChange={setPage}
            emptyMessage="No threat records match the filters."
          />
        )}
      </Card>

      <Card>
        <CardHeader title="Sources" subtitle="Configured threat dataset sources" />
        <div className="flex flex-wrap gap-2 p-4">
          {(stats?.sources ?? []).map((source) => (
            <Badge key={source.source} className="bg-slate-100 text-slate-600 border-slate-200">
              {source.source} · {source.count}
            </Badge>
          ))}
        </div>
      </Card>

      <p className="text-center text-[11px] text-slate-400">
        Threat records are indicators from configured datasets — a match is not, by itself, a determination of unlawful activity.
      </p>
    </div>
  );
}

export default function ThreatIntelligencePage() {
  return (
    <Suspense fallback={<Card className="p-6"><Spinner /> Loading…</Card>}>
      <ThreatsInner />
    </Suspense>
  );
}
