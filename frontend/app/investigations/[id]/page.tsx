"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, FileText, Link2, Paperclip, Plus } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton, EmptyState } from "@/components/common/ui";
import { Modal } from "@/components/common/modal";
import { CASE_STATUSES, CASE_STATUS_STYLES, EVIDENCE_TYPES, PRIORITY_STYLES } from "@/lib/constants";
import { formatDateTime, titleCase, timeAgo, truncateMiddle } from "@/lib/formatters";
import type { CaseDetail } from "@/types";

export default function CaseDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const queryClient = useQueryClient();
  const [walletInput, setWalletInput] = useState("");
  const [evidenceModal, setEvidenceModal] = useState(false);
  const [evidenceForm, setEvidenceForm] = useState({ title: "", evidence_type: "Document", description: "", content_text: "" });
  const [file, setFile] = useState<File | null>(null);

  const { data: caseDetail, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["case", id],
    queryFn: async () => (await api.get<CaseDetail>(`/cases/${id}`)).data,
  });

  const updateCase = useMutation({
    mutationFn: async (payload: Record<string, string>) => (await api.patch<CaseDetail>(`/cases/${id}`, payload)).data,
    onSuccess: () => {
      toast.success("Case updated");
      void queryClient.invalidateQueries({ queryKey: ["case", id] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Update failed"),
  });

  const linkWallet = useMutation({
    mutationFn: async (address: string) => (await api.post<{ investigation_id: number }>(`/cases/${id}/investigations`, { wallet_address: address })).data,
    onSuccess: () => {
      toast.success("Wallet investigation linked");
      setWalletInput("");
      void queryClient.invalidateQueries({ queryKey: ["case", id] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to link wallet"),
  });

  const addNote = useMutation({
    mutationFn: async (note: string) => (await api.post(`/cases/${id}/notes`, { note })).data,
    onSuccess: () => {
      toast.success("Note added to timeline");
      void queryClient.invalidateQueries({ queryKey: ["case", id] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to add note"),
  });

  const uploadEvidence = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("title", evidenceForm.title);
      form.append("evidence_type", evidenceForm.evidence_type);
      if (evidenceForm.description) form.append("description", evidenceForm.description);
      if (file) form.append("file", file);
      else form.append("content_text", evidenceForm.content_text);
      return (await api.upload(`/cases/${id}/evidence`, form)).data;
    },
    onSuccess: () => {
      toast.success("Evidence attached");
      setEvidenceModal(false);
      setEvidenceForm({ title: "", evidence_type: "Document", description: "", content_text: "" });
      setFile(null);
      void queryClient.invalidateQueries({ queryKey: ["case", id] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Upload failed"),
  });

  const generateReport = useMutation({
    mutationFn: async (wallet: string) => (await api.post<{ id: string }>("/reports/generate", { wallet_address: wallet, case_id: Number(id) })).data,
    onSuccess: (report) => {
      toast.success("Report generated");
      void queryClient.invalidateQueries({ queryKey: ["case", id] });
      window.location.href = `/reports?report=${report.id}`;
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Report generation failed"),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Card className="p-5">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-3 h-20 w-full" />
        </Card>
      </div>
    );
  }

  if (isError || !caseDetail) {
    return (
      <Card>
        <EmptyState title="Case not available" description={(error as Error)?.message ?? "This case does not exist."} action={<Button size="sm" variant="secondary" onClick={() => void refetch()}>Retry</Button>} />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <Link href="/investigations" className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-primary">
          <ArrowLeft size={12} /> All cases
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <h2 className="text-lg font-semibold text-ink">
            <span className="font-mono">{caseDetail.case_number}</span> — {caseDetail.title}
          </h2>
          <Badge className={CASE_STATUS_STYLES[caseDetail.status]}>{titleCase(caseDetail.status)}</Badge>
          <Badge className={PRIORITY_STYLES[caseDetail.priority]}>{caseDetail.priority}</Badge>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Case overview" subtitle={`Opened ${timeAgo(caseDetail.created_at)} · by ${caseDetail.investigator}`} />
          <div className="space-y-3 p-5">
            <p className="text-sm text-slate-600">{caseDetail.description ?? "No description."}</p>
            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
              <label className="text-xs font-medium text-slate-500" htmlFor="case-status">Status</label>
              <Select
                id="case-status"
                value={caseDetail.status}
                onChange={(e) => updateCase.mutate({ status: e.target.value })}
                className="w-48 py-1.5 text-xs"
                aria-label="Case status"
              >
                {CASE_STATUSES.map((status) => (
                  <option key={status} value={status}>
                    {titleCase(status)}
                  </option>
                ))}
              </Select>
              <label className="ml-2 text-xs font-medium text-slate-500" htmlFor="case-priority">Priority</label>
              <Select
                id="case-priority"
                value={caseDetail.priority}
                onChange={(e) => updateCase.mutate({ priority: e.target.value })}
                className="w-36 py-1.5 text-xs"
                aria-label="Case priority"
              >
                {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((priority) => (
                  <option key={priority} value={priority}>
                    {priority}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Link a wallet investigation" subtitle="Runs the pipeline if the wallet was never investigated" />
          <div className="space-y-2 p-5">
            <div className="flex gap-2">
              <Input value={walletInput} onChange={(e) => setWalletInput(e.target.value)} placeholder="Wallet address" className="font-mono text-xs" aria-label="Wallet address to link" />
              <Button size="sm" disabled={walletInput.trim().length < 4 || linkWallet.isPending} onClick={() => linkWallet.mutate(walletInput.trim())}>
                {linkWallet.isPending ? <Spinner className="border-white/40" /> : <Link2 size={13} />} Link
              </Button>
            </div>
            {caseDetail.investigations.length === 0 ? (
              <p className="text-[11px] text-slate-400">No linked investigations yet.</p>
            ) : (
              <ul className="space-y-1.5 pt-1">
                {caseDetail.investigations.map((investigation) => (
                  <li key={investigation.id} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
                    <Link href={`/wallet?address=${encodeURIComponent(investigation.wallet_address)}`} className="font-mono text-xs text-primary hover:underline">
                      {truncateMiddle(investigation.wallet_address, 14, 6)}
                    </Link>
                    <Badge className={investigation.risk_level === "HIGH" ? "bg-red-50 text-red-700 border-red-200" : investigation.risk_level === "ELEVATED" ? "bg-orange-50 text-orange-700 border-orange-200" : "bg-emerald-50 text-emerald-700 border-emerald-200"}>
                      {investigation.risk_level ?? "N/A"}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Evidence"
            subtitle={`${caseDetail.evidence.length} item(s) with SHA-256 integrity`}
            action={
              <div className="flex gap-1.5">
                <Button size="sm" variant="secondary" onClick={() => setEvidenceModal(true)}>
                  <Paperclip size={12} /> Attach
                </Button>
                <Link href="/evidence">
                  <Button size="sm" variant="ghost">Repository</Button>
                </Link>
              </div>
            }
          />
          {caseDetail.evidence.length === 0 ? (
            <EmptyState title="No evidence attached" description="Screenshots, documents, API responses and notes appear here." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {caseDetail.evidence.map((item) => (
                <li key={item.id} className="px-5 py-2.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-medium text-ink">{item.title}</span>
                    <Badge>{item.type}</Badge>
                  </div>
                  <p className="mt-0.5 font-mono text-[10px] text-slate-400" title={item.sha256 ?? ""}>
                    SHA-256: {item.sha256 ? `${item.sha256.slice(0, 24)}…` : "—"}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader title="Case timeline" subtitle="Chronological record of case activity" />
          {caseDetail.timeline.length === 0 ? (
            <EmptyState title="No timeline events" />
          ) : (
            <ol className="thin-scroll max-h-[320px] overflow-y-auto px-5 py-3">
              {caseDetail.timeline.map((event) => (
                <li key={event.id} className="relative border-l border-slate-200 pb-3 pl-4 last:pb-0">
                  <span className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-primary" aria-hidden />
                  <p className="text-xs font-medium text-ink">{titleCase(event.event_type)}</p>
                  <p className="text-[11px] text-slate-500">{event.description}</p>
                  <p className="text-[10px] text-slate-400">{formatDateTime(event.created_at)}</p>
                </li>
              ))}
            </ol>
          )}
          <div className="border-t border-slate-100 p-4">
            <textarea
              rows={2}
              value={evidenceForm.content_text && evidenceModal === false ? evidenceForm.content_text : ""}
              onChange={(e) => setEvidenceForm({ ...evidenceForm, content_text: e.target.value })}
              placeholder="Add an analyst note to the timeline…"
              aria-label="New timeline note"
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-primary focus:outline focus:outline-2 focus:outline-primary-100"
            />
            <Button size="sm" variant="secondary" className="mt-2" disabled={!evidenceForm.content_text.trim() || addNote.isPending} onClick={() => { addNote.mutate(evidenceForm.content_text.trim()); setEvidenceForm({ ...evidenceForm, content_text: "" }); }}>
              <Plus size={12} /> Add note
            </Button>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Reports" subtitle="Generate a forensic report from this case" />
        <div className="flex flex-wrap items-center gap-2 p-5">
          {caseDetail.investigations.length > 0 ? (
            caseDetail.investigations.map((investigation) => (
              <Button key={investigation.id} size="sm" variant="secondary" disabled={generateReport.isPending} onClick={() => generateReport.mutate(investigation.wallet_address)}>
                <FileText size={13} /> Report for {truncateMiddle(investigation.wallet_address, 12, 6)}
              </Button>
            ))
          ) : (
            <p className="text-xs text-slate-400">Link a wallet investigation first, then generate reports from here.</p>
          )}
          <Link href="/reports" className="ml-auto">
            <Button size="sm" variant="ghost">All reports</Button>
          </Link>
        </div>
      </Card>

      <Modal open={evidenceModal} onClose={() => setEvidenceModal(false)} title="Attach evidence">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="ev-title">Title</label>
            <Input id="ev-title" value={evidenceForm.title} onChange={(e) => setEvidenceForm({ ...evidenceForm, title: e.target.value })} className="mt-1" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="ev-type">Type</label>
            <Select id="ev-type" value={evidenceForm.evidence_type} onChange={(e) => setEvidenceForm({ ...evidenceForm, evidence_type: e.target.value })} className="mt-1 w-full">
              {EVIDENCE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="ev-file">File (optional)</label>
            <input id="ev-file" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-xs text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-xs file:font-medium hover:file:bg-slate-200" />
            <p className="mt-1 text-[10px] text-slate-400">Allowed: images, PDF, TXT, CSV, JSON, ZIP, log, md, har (max 10 MB). SHA-256 computed automatically.</p>
          </div>
          {!file ? (
            <div>
              <label className="text-xs font-medium text-slate-600">Note content (when no file)</label>
              <textarea
                rows={3}
                value={evidenceForm.content_text}
                onChange={(e) => setEvidenceForm({ ...evidenceForm, content_text: e.target.value })}
                aria-label="Note content"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:outline focus:outline-2 focus:outline-primary-100"
              />
            </div>
          ) : null}
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" size="sm" onClick={() => setEvidenceModal(false)}>Cancel</Button>
            <Button size="sm" onClick={() => uploadEvidence.mutate()} disabled={uploadEvidence.isPending || !evidenceForm.title.trim() || (!file && !evidenceForm.content_text.trim())}>
              {uploadEvidence.isPending ? <Spinner className="border-white/40" /> : null} Attach
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
