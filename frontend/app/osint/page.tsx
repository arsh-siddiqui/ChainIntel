"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ExternalLink, ShieldQuestion, Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, EmptyState, Skeleton, TextareaLike } from "@/components/common/ui";
import { OSINT_STATUS_STYLES } from "@/lib/constants";
import { confidencePercent } from "@/lib/formatters";
import { restrictedSourceSchema, type RestrictedSourceForm } from "@/lib/validators";
import type { OSINTCorrelation, OSINTResult, OSINTSourceStatus, ValidationResult } from "@/types";

interface RestrictedRecord {
  id: number;
  wallet_address: string;
  source: string;
  record_type: string | null;
  finding: string | null;
  status: string;
  confidence: number;
  reference_url: string | null;
  notes: string | null;
  observed_at: string;
  is_demo: boolean;
}

const RECORD_TYPE_LABELS: Record<string, string> = {
  VERIFIED_SOURCE: "Verified Source",
  IMPORTED_INTELLIGENCE: "Imported Intelligence",
  ANALYST_NOTE: "Analyst Note",
  UNAVAILABLE: "Unavailable",
};

export default function OsintPage() {
  const queryClient = useQueryClient();
  const [address, setAddress] = useState("");
  const [applied, setApplied] = useState("");
  const [form, setForm] = useState<RestrictedSourceForm>({ wallet_address: "", source: "", record_type: "ANALYST_NOTE", finding: "", reference_url: "", confidence: 0.5 });
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["osint", applied],
    queryFn: async () =>
      (await api.get<{ validation: ValidationResult; correlation: OSINTCorrelation; restricted_count: number }>(`/osint/search/${encodeURIComponent(applied)}`)).data,
    enabled: applied.length >= 4,
  });

  const { data: restricted } = useQuery({
    queryKey: ["restricted", applied],
    queryFn: async () => (await api.get<{ records: RestrictedRecord[]; disclaimer: string }>(`/osint/restricted/${encodeURIComponent(applied)}`)).data,
    enabled: applied.length >= 4,
  });

  const { data: sources } = useQuery({
    queryKey: ["osint-sources"],
    queryFn: async () => (await api.get<{ sources: OSINTSourceStatus[]; note: string }>("/osint/sources")).data,
  });

  const addRecordMutation = useMutation({
    mutationFn: async (payload: RestrictedSourceForm) => (await api.post<RestrictedRecord>("/osint/restricted", { ...payload, wallet_address: applied, reference_url: payload.reference_url || undefined })).data,
    onSuccess: () => {
      toast.success("Restricted-source record added");
      setForm({ wallet_address: "", source: "", record_type: "ANALYST_NOTE", finding: "", reference_url: "", confidence: 0.5 });
      void queryClient.invalidateQueries({ queryKey: ["restricted", applied] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to add record"),
  });

  const submitRecord = () => {
    const parsed = restrictedSourceSchema.safeParse(form);
    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Invalid form");
      return;
    }
    setFormError(null);
    addRecordMutation.mutate(parsed.data);
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink">OSINT Correlation</h2>
        <p className="text-xs text-slate-500">Source-by-source wallet reputation. Link-only sources never fabricate results.</p>
      </div>

      <Card className="p-4">
        <form
          className="flex flex-col gap-2 md:flex-row"
          onSubmit={(event) => {
            event.preventDefault();
            setApplied(address.trim());
          }}
        >
          <Input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Wallet address" className="font-mono md:flex-1" aria-label="Wallet address" />
          <Button type="submit" disabled={address.trim().length < 4 || isLoading} className="md:w-40">
            {isLoading ? <Spinner className="border-white/40" /> : <Search size={14} />} Correlate
          </Button>
        </form>
      </Card>

      {isError ? (
        <Card>
          <EmptyState title="Lookup failed" description={(error as Error).message} action={<Button size="sm" variant="secondary" onClick={() => void refetch()}>Retry</Button>} />
        </Card>
      ) : null}

      {!applied && !isLoading ? (
        <Card>
          <EmptyState icon={<ShieldQuestion size={36} />} title="No address correlated yet" description="Enter a wallet address above to correlate reputation across public sources." />
        </Card>
      ) : null}

      {isLoading && applied ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i} className="p-4">
              <Skeleton className="h-4 w-56" />
              <Skeleton className="mt-2 h-3 w-full" />
            </Card>
          ))}
        </div>
      ) : null}

      {data ? (
        <>
          {data.validation.valid ? null : (
            <Card className="border-amber-200 bg-amber-50 p-4">
              <p className="text-sm text-amber-800">{data.validation.reason}</p>
            </Card>
          )}
          <Card>
            <CardHeader
              title={`Results for ${applied.slice(0, 24)}…`}
              subtitle={data.correlation.note}
              action={<Badge className="bg-purple-50 text-purple-700 border-purple-200">{data.correlation.found_count}/{data.correlation.provider_count} reporting</Badge>}
            />
            <ul className="divide-y divide-slate-100">
              {data.correlation.results.map((result: OSINTResult) => (
                <li key={result.source_name} className="px-5 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-ink">{result.source_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {result.status === "FOUND" ? <span className="text-[11px] font-medium text-purple-700">{confidencePercent(result.confidence)}</span> : null}
                      <Badge className={OSINT_STATUS_STYLES[result.status] ?? "bg-slate-100 text-slate-600 border-slate-200"}>{result.status.replace("_", " ")}</Badge>
                    </div>
                  </div>
                  {result.finding ? <p className="mt-1 text-xs text-slate-600">{result.finding}</p> : null}
                  {result.notes ? <p className="mt-0.5 text-[11px] text-slate-400">{result.notes}</p> : null}
                  <div className="mt-1.5 flex gap-3">
                    {result.reference_url ? (
                      <a href={result.reference_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
                        <ExternalLink size={11} /> Reference
                      </a>
                    ) : null}
                    {result.external_search_url ? (
                      <a href={result.external_search_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-primary hover:underline">
                        <ExternalLink size={11} /> Manual lookup
                      </a>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </>
      ) : null}

      {applied ? (
        <Card>
          <CardHeader
            title="Dark-Web / Restricted Source Correlation"
            subtitle="Metadata/evidence correlation — not a crawler. ChainIntel never claims to have searched the dark web."
          />
          <div className="border-b border-slate-100 bg-slate-50 px-5 py-2.5">
            <p className="text-[11px] text-slate-500">{restricted?.disclaimer ?? "Loading…"}</p>
          </div>
          {restricted && restricted.records.length > 0 ? (
            <ul className="divide-y divide-slate-100">
              {restricted.records.map((record) => (
                <li key={record.id} className="px-5 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-purple-50 text-purple-700 border-purple-200">{RECORD_TYPE_LABELS[record.record_type ?? "ANALYST_NOTE"] ?? record.record_type}</Badge>
                      <span className="text-sm font-medium text-ink">{record.source}</span>
                    </div>
                    <span className="text-[11px] text-slate-400">{confidencePercent(record.confidence)} confidence</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">{record.finding}</p>
                  {record.reference_url ? (
                    <a href={record.reference_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
                      <ExternalLink size={11} /> Reference
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No restricted-source records" description="No configured restricted source has reported anything for this address. Analyst-entered records appear here." />
          )}
          <div className="space-y-3 border-t border-slate-100 p-5">
            <p className="text-xs font-semibold text-ink">Add analyst / imported record</p>
            <div className="grid gap-2 md:grid-cols-3">
              <Input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} placeholder="Source name" aria-label="Record source" />
              <Select value={form.record_type} onChange={(e) => setForm({ ...form, record_type: e.target.value as RestrictedSourceForm["record_type"] })} aria-label="Record type">
                {Object.entries(RECORD_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
              <Input type="number" min={0} max={1} step={0.05} value={form.confidence} onChange={(e) => setForm({ ...form, confidence: Number(e.target.value) })} aria-label="Confidence (0-1)" />
            </div>
            <TextareaLike value={form.finding} onChange={(value) => setForm({ ...form, finding: value })} placeholder="Finding description (what was observed, where, when)…" aria-label="Finding" />
            <div className="flex gap-2">
              <Input value={form.reference_url} onChange={(e) => setForm({ ...form, reference_url: e.target.value })} placeholder="Reference URL (optional)" className="flex-1" aria-label="Reference URL" />
              <Button size="sm" onClick={submitRecord} disabled={addRecordMutation.isPending}>
                {addRecordMutation.isPending ? <Spinner className="border-white/40" /> : null} Add record
              </Button>
            </div>
            {formError ? <p className="text-xs text-red-600">{formError}</p> : null}
          </div>
        </Card>
      ) : null}

      <Card>
        <CardHeader title="Configured OSINT sources" subtitle="Link-only public sources and restricted analyst records" />
        <div className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-4">
          {(sources?.sources ?? []).map((source) => (
            <div key={source.name} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
              <span className="text-xs font-medium text-ink">{source.name}</span>
              <Badge className="bg-slate-100 text-slate-600 border-slate-200">Link-only</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
