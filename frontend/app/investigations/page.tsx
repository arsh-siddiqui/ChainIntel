"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FolderLock, Plus } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton, TextareaLike, EmptyState } from "@/components/common/ui";
import { DataTable, type Column } from "@/components/common/data-table";
import { Modal } from "@/components/common/modal";
import { CASE_PRIORITIES, CASE_STATUSES, CASE_STATUS_STYLES, PRIORITY_STYLES } from "@/lib/constants";
import { timeAgo, titleCase } from "@/lib/formatters";
import { caseSchema, type CaseForm } from "@/lib/validators";
import type { CaseRecord, PageMeta } from "@/types";

function CasesInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(searchParams.get("new") === "1");
  const [form, setForm] = useState<CaseForm>({ title: "", description: "", priority: "MEDIUM" });
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["cases", status, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: "15" });
      if (status) params.set("status", status);
      const response = await api.get<CaseRecord[]>(`/cases?${params.toString()}`);
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
  });

  const createCase = useMutation({
    mutationFn: async (payload: CaseForm) => (await api.post<CaseRecord>("/cases", { ...payload, description: payload.description || undefined })).data,
    onSuccess: (created) => {
      toast.success(`Case ${created.case_number} created`);
      setModal(false);
      setForm({ title: "", description: "", priority: "MEDIUM" });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      router.push(`/investigations/${created.id}`);
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to create case"),
  });

  const submit = () => {
    const parsed = caseSchema.safeParse(form);
    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Invalid form");
      return;
    }
    setFormError(null);
    createCase.mutate(parsed.data);
  };

  const columns: Column<CaseRecord>[] = [
    { key: "number", header: "Case ID", render: (c) => <Link href={`/investigations/${c.id}`} className="font-mono text-xs font-semibold text-primary hover:underline">{c.case_number}</Link> },
    { key: "title", header: "Title", render: (c) => <Link href={`/investigations/${c.id}`} className="text-sm font-medium text-ink hover:text-primary">{c.title}</Link> },
    { key: "status", header: "Status", render: (c) => <Badge className={CASE_STATUS_STYLES[c.status]}>{titleCase(c.status)}</Badge> },
    { key: "priority", header: "Priority", render: (c) => <Badge className={PRIORITY_STYLES[c.priority]}>{c.priority}</Badge> },
    { key: "investigator", header: "Investigator", render: (c) => <span className="text-xs text-slate-500">{c.investigator}</span> },
    { key: "created", header: "Created", render: (c) => <span className="text-xs text-slate-500">{timeAgo(c.created_at)}</span> },
    { key: "updated", header: "Updated", align: "right", render: (c) => <span className="text-xs text-slate-500">{timeAgo(c.updated_at)}</span> },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">Investigation Cases</h2>
          <p className="text-xs text-slate-500">Organize wallets, evidence, findings and reports into casework.</p>
        </div>
        <Button onClick={() => setModal(true)}>
          <Plus size={14} /> Create Case
        </Button>
      </div>

      <Card>
        <CardHeader
          title="All cases"
          subtitle="Click a case to open its workspace"
          action={
            <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Status filter" className="w-48 py-1.5 text-xs">
              <option value="">All statuses</option>
              {CASE_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {titleCase(s)}
                </option>
              ))}
            </Select>
          }
        />
        {isLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <DataTable columns={columns} rows={data?.rows ?? []} rowKey={(c) => c.id} meta={data?.meta} onPageChange={setPage} emptyMessage="No cases yet — create one to get started." />
        )}
      </Card>

      {!(data?.rows ?? []).length && !isLoading ? (
        <Card>
          <EmptyState icon={<FolderLock size={32} />} title="No cases found" description="Investigation cases group wallet investigations, evidence and reports." />
        </Card>
      ) : null}

      <Modal open={modal} onClose={() => setModal(false)} title="Create investigation case">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="case-title">Title</label>
            <Input id="case-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Ransomware payment trace" className="mt-1" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600">Description</label>
            <TextareaLike value={form.description ?? ""} onChange={(value) => setForm({ ...form, description: value })} placeholder="Scope, objectives, related wallets…" rows={4} ariaLabel="Case description" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="case-priority">Priority</label>
            <Select id="case-priority" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value as CaseForm["priority"] })} className="mt-1 w-full">
              {CASE_PRIORITIES.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </Select>
          </div>
          {formError ? <p className="text-xs text-red-600">{formError}</p> : null}
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" size="sm" onClick={() => setModal(false)}>Cancel</Button>
            <Button size="sm" onClick={submit} disabled={createCase.isPending}>
              {createCase.isPending ? <Spinner className="border-white/40" /> : null} Create case
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default function InvestigationsPage() {
  return (
    <Suspense fallback={<Card className="p-6"><Spinner /> Loading…</Card>}>
      <CasesInner />
    </Suspense>
  );
}
