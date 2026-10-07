"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Download, FileCheck2, ShieldCheck } from "lucide-react";
import { api, apiDownload } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton, EmptyState } from "@/components/common/ui";
import { DataTable, type Column } from "@/components/common/data-table";
import { EVIDENCE_TYPES } from "@/lib/constants";
import { formatDateTime, titleCase, truncateMiddle } from "@/lib/formatters";
import type { EvidenceRecord, PageMeta } from "@/types";

export default function EvidencePage() {
  const [search, setSearch] = useState("");
  const [applied, setApplied] = useState("");
  const [type, setType] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["evidence", applied, type, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (applied) params.set("search", applied);
      if (type) params.set("type", type);
      const response = await api.get<EvidenceRecord[]>(`/evidence?${params.toString()}`);
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
  });

  const verify = useQuery({
    queryKey: ["evidence-verify", applied],
    queryFn: async () => {
      const params = new URLSearchParams({ page: "1", page_size: "50" });
      if (applied) params.set("search", applied);
      const response = await api.get<EvidenceRecord[]>(`/evidence?${params.toString()}`);
      const results = await Promise.all(
        response.data.slice(0, 20).map(async (item) => {
          const detail = await api.get<{ integrity_verified: boolean }>(`/evidence/${item.id}`);
          return { id: item.id, ok: detail.data.integrity_verified };
        }),
      );
      return Object.fromEntries(results.map((r) => [r.id, r.ok]));
    },
    enabled: Boolean(data?.rows.length),
  });

  const columns: Column<EvidenceRecord>[] = [
    { key: "id", header: "ID", render: (e) => <span className="font-mono text-xs text-slate-500">#{e.id}</span> },
    { key: "type", header: "Type", render: (e) => <Badge>{e.type}</Badge> },
    { key: "title", header: "Title", render: (e) => <span className="text-xs font-medium text-ink">{e.title}</span> },
    {
      key: "case",
      header: "Case",
      render: (e) =>
        e.case_id ? (
          <Link href={`/investigations/${e.case_id}`} className="text-xs text-primary hover:underline">
            Case #{e.case_id}
          </Link>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        ),
    },
    { key: "source", header: "Source", render: (e) => <span className="max-w-[160px] truncate text-[11px] text-slate-500">{e.source ?? "—"}</span> },
    {
      key: "sha",
      header: "SHA-256",
      render: (e) => (
        <span className="font-mono text-[10px] text-slate-400" title={e.sha256 ?? ""}>
          {e.sha256 ? `${e.sha256.slice(0, 16)}…` : "—"}
        </span>
      ),
    },
    {
      key: "integrity",
      header: "Integrity",
      render: (e) => {
        if (verify.isLoading) return <Spinner className="h-3 w-3" />;
        const ok = verify.data?.[e.id];
        return ok === undefined ? (
          <span className="text-[11px] text-slate-400">—</span>
        ) : ok ? (
          <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200" title="Recomputed SHA-256 matches stored hash">
            <ShieldCheck size={11} /> Verified
          </Badge>
        ) : (
          <Badge className="bg-red-50 text-red-700 border-red-200" title="Stored hash does not match recomputed hash">
            Mismatch
          </Badge>
        );
      },
    },
    { key: "created", header: "Created", render: (e) => <span className="text-xs text-slate-500">{formatDateTime(e.created_at)}</span> },
    {
      key: "download",
      header: "",
      align: "right",
      render: (e) =>
        e.has_file ? (
          <Button variant="ghost" size="sm" onClick={() => apiDownload(`/evidence/${e.id}/download`, e.file_name ?? `evidence-${e.id}`)} aria-label={`Download ${e.title}`}>
            <Download size={13} />
          </Button>
        ) : (
          <span className="text-[11px] text-slate-400">note</span>
        ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-heading text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">Chain of Custody Evidence Vault</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Chain-of-custody repository. Uploaded files are hashed with SHA-256; integrity is re-verified on demand.</p>
        </div>
        <Badge className="bg-purple-50 text-purple-700 border-purple-200">
          <FileCheck2 size={12} /> {data?.meta.total ?? "—"} records
        </Badge>
      </div>

      <Card className="p-4">
        <div className="flex flex-col gap-2 md:flex-row">
          <form
            className="md:flex-1"
            onSubmit={(event) => {
              event.preventDefault();
              setApplied(search);
              setPage(1);
            }}
          >
            <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search evidence titles and descriptions…" aria-label="Search evidence" />
          </form>
          <Select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }} aria-label="Type filter" className="md:w-56">
            <option value="">All types</option>
            {EVIDENCE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      <Card>
        <CardHeader title="Evidence repository" subtitle="Attach evidence from any case workspace" />
        {isLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (data?.rows ?? []).length === 0 ? (
          <EmptyState title="No evidence yet" description="Open a case and attach screenshots, documents, API responses or analyst notes." action={<Link href="/investigations"><Button size="sm">Open cases</Button></Link>} />
        ) : (
          <DataTable columns={columns} rows={data?.rows ?? []} rowKey={(e) => e.id} meta={data?.meta} onPageChange={setPage} />
        )}
      </Card>
    </div>
  );
}
