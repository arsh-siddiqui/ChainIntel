"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bell, Plus, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton, EmptyState } from "@/components/common/ui";
import { DataTable, type Column } from "@/components/common/data-table";
import { Modal } from "@/components/common/modal";
import { ALERT_STATUSES, ALERT_STATUS_STYLES, SEVERITY_STYLES } from "@/lib/constants";
import { timeAgo, truncateMiddle, titleCase } from "@/lib/formatters";
import { monitorSchema, type MonitorForm } from "@/lib/validators";
import type { Alert, Monitor, PageMeta } from "@/types";

function ruleSummary(rules: Monitor["rules"]): string {
  const parts: string[] = [];
  if (rules.direction && rules.direction !== "any") parts.push(`${rules.direction} txs`);
  if (rules.amount_threshold) parts.push(`> ${rules.amount_threshold}`);
  if (rules.on_threat_match) parts.push("threat match");
  if (rules.flagged_counterparty) parts.push("flagged counterparty");
  return parts.length ? parts.join(" · ") : "any transaction";
}

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [alertStatus, setAlertStatus] = useState("");
  const [alertPage, setAlertPage] = useState(1);
  const [monitorModal, setMonitorModal] = useState(false);
  const [form, setForm] = useState<MonitorForm>({ wallet_address: "", label: "", direction: "any", amount_threshold: undefined, on_threat_match: false, flagged_counterparty: false });
  const [formError, setFormError] = useState<string | null>(null);

  const { data: monitorData, isLoading: monitorsLoading } = useQuery({
    queryKey: ["monitors"],
    queryFn: async () => (await api.get<Monitor[]>("/alerts/monitors")).data,
  });

  const { data: alertData, isLoading: alertsLoading } = useQuery({
    queryKey: ["alerts", alertStatus, alertPage],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(alertPage), page_size: "15" });
      if (alertStatus) params.set("status", alertStatus);
      const response = await api.get<Alert[]>(`/alerts?${params.toString()}`);
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
    refetchInterval: 30_000,
  });

  const createMonitor = useMutation({
    mutationFn: async (payload: MonitorForm) =>
      (
        await api.post<Monitor>("/alerts/monitor", {
          wallet_address: payload.wallet_address,
          blockchain: "auto",
          label: payload.label || undefined,
          rules: {
            direction: payload.direction,
            amount_threshold: payload.amount_threshold ?? null,
            on_threat_match: payload.on_threat_match,
            flagged_counterparty: payload.flagged_counterparty,
          },
        })
      ).data,
    onSuccess: () => {
      toast.success("Monitoring rule created");
      setMonitorModal(false);
      setForm({ wallet_address: "", label: "", direction: "any", amount_threshold: undefined, on_threat_match: false, flagged_counterparty: false });
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to create monitor"),
  });

  const toggleMonitor = useMutation({
    mutationFn: async (monitor: Monitor) => (await api.patch<Monitor>(`/alerts/monitors/${monitor.id}`, { status: monitor.status === "ACTIVE" ? "PAUSED" : "ACTIVE" })).data,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["monitors"] }),
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to update monitor"),
  });

  const deleteMonitor = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/alerts/monitors/${id}`)).data,
    onSuccess: () => {
      toast.success("Monitor removed");
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to remove monitor"),
  });

  const updateAlert = useMutation({
    mutationFn: async (input: { id: number; status: string }) => (await api.patch<Alert>(`/alerts/${input.id}`, { status: input.status })).data,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["alerts"] }),
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to update alert"),
  });

  const submitMonitor = () => {
    const parsed = monitorSchema.safeParse(form);
    if (!parsed.success) {
      setFormError(parsed.error.issues[0]?.message ?? "Invalid form");
      return;
    }
    setFormError(null);
    createMonitor.mutate(parsed.data);
  };

  const alertColumns: Column<Alert>[] = [
    { key: "severity", header: "Severity", render: (a) => <Badge className={SEVERITY_STYLES[a.severity]}>{a.severity}</Badge> },
    { key: "wallet", header: "Wallet", render: (a) => <span className="font-mono text-xs">{truncateMiddle(a.wallet_address, 14, 6)}</span> },
    {
      key: "rule",
      header: "Rule",
      render: (a) => <span className="text-[11px] text-slate-500">{a.rule ? ruleSummary(a.rule as Monitor["rules"]) : "—"}</span>,
    },
    { key: "title", header: "Event", render: (a) => <span className="text-xs text-ink">{a.title}</span> },
    { key: "message", header: "Detail", render: (a) => <span className="line-clamp-2 max-w-[280px] text-[11px] text-slate-500">{a.message}</span> },
    { key: "tx", header: "Transaction", render: (a) => <span className="font-mono text-[11px] text-slate-500">{a.transaction_hash ? truncateMiddle(a.transaction_hash, 10, 4) : "—"}</span> },
    { key: "created", header: "Created", render: (a) => <span className="text-xs text-slate-500">{timeAgo(a.created_at)}</span> },
    { key: "status", header: "Status", render: (a) => <Badge className={ALERT_STATUS_STYLES[a.status]}>{titleCase(a.status)}</Badge> },
    {
      key: "action",
      header: "Action",
      render: (a) => (
        <Select
          value={a.status}
          onChange={(event) => updateAlert.mutate({ id: a.id, status: event.target.value })}
          className="w-36 py-1 text-[11px]"
          aria-label={`Update status for alert ${a.id}`}
        >
          {ALERT_STATUSES.map((status) => (
            <option key={status} value={status}>
              {titleCase(status)}
            </option>
          ))}
        </Select>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-heading text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">Real-Time Alerts & Threat Monitors</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Wallet monitoring rules and generated alerts, evaluated against live blockchain activity.</p>
        </div>
        <Button onClick={() => setMonitorModal(true)}>
          <Plus size={14} /> Add Monitored Wallet
        </Button>
      </div>

      <Card>
        <CardHeader title="Monitored wallets" subtitle="Active rules evaluated by the monitoring engine" />
        {monitorsLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (monitorData ?? []).length === 0 ? (
          <EmptyState icon={<Bell size={32} />} title="No monitored wallets" description="Add a monitoring rule to receive alerts on new activity." action={<Button size="sm" onClick={() => setMonitorModal(true)}>Add wallet</Button>} />
        ) : (
          <ul className="divide-y divide-slate-100">
            {(monitorData ?? []).map((monitor) => (
              <li key={monitor.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                <span className={`h-2 w-2 rounded-full ${monitor.status === "ACTIVE" ? "bg-emerald-500" : "bg-slate-300"}`} aria-hidden />
                <div className="min-w-0 flex-1">
                  <p className="truncate font-mono text-xs font-medium text-ink">{monitor.wallet_address}</p>
                  <p className="text-[11px] text-slate-500">
                    Rule: {ruleSummary(monitor.rules)} · Last checked: {monitor.last_checked ? timeAgo(monitor.last_checked) : "never"}
                  </p>
                </div>
                <Badge className={monitor.status === "ACTIVE" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-500 border-slate-200"}>{monitor.status}</Badge>
                <Button variant="secondary" size="sm" onClick={() => toggleMonitor.mutate(monitor)}>
                  {monitor.status === "ACTIVE" ? "Pause" : "Resume"}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => deleteMonitor.mutate(monitor.id)} aria-label={`Remove monitor for ${monitor.wallet_address}`}>
                  <Trash2 size={13} className="text-red-500" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <CardHeader
          title="Alerts"
          subtitle="Generated monitoring alerts"
          action={
            <Select value={alertStatus} onChange={(e) => { setAlertStatus(e.target.value); setAlertPage(1); }} aria-label="Status filter" className="w-44 py-1.5 text-xs">
              <option value="">All statuses</option>
              {ALERT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {titleCase(status)}
                </option>
              ))}
            </Select>
          }
        />
        {alertsLoading ? (
          <div className="space-y-2 p-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-9 w-full" />
            ))}
          </div>
        ) : (
          <DataTable columns={alertColumns} rows={alertData?.rows ?? []} rowKey={(a) => a.id} meta={alertData?.meta} onPageChange={setAlertPage} emptyMessage="No alerts match the current filter." />
        )}
      </Card>

      <Modal open={monitorModal} onClose={() => setMonitorModal(false)} title="Add monitored wallet">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="monitor-wallet">Wallet address</label>
            <Input id="monitor-wallet" value={form.wallet_address} onChange={(e) => setForm({ ...form, wallet_address: e.target.value })} placeholder="e.g. bc1q... or 0x..." className="mt-1 font-mono text-xs" />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="monitor-label">Label (optional)</label>
            <Input id="monitor-label" value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} placeholder="e.g. Ransom collection wallet" className="mt-1" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs font-medium text-slate-600" htmlFor="monitor-direction">Direction</label>
              <Select id="monitor-direction" value={form.direction} onChange={(e) => setForm({ ...form, direction: e.target.value as MonitorForm["direction"] })} className="mt-1 w-full">
                <option value="any">Any transaction</option>
                <option value="incoming">Incoming only</option>
                <option value="outgoing">Outgoing only</option>
              </Select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600" htmlFor="monitor-threshold">Amount threshold</label>
              <Input id="monitor-threshold" type="number" step="any" min={0} value={form.amount_threshold ?? ""} onChange={(e) => setForm({ ...form, amount_threshold: e.target.value === "" ? undefined : Number(e.target.value) })} placeholder="e.g. 1.0" className="mt-1" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-600">
            <input type="checkbox" checked={form.on_threat_match} onChange={(e) => setForm({ ...form, on_threat_match: e.target.checked })} />
            Alert when the wallet matches threat intelligence
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-600">
            <input type="checkbox" checked={form.flagged_counterparty} onChange={(e) => setForm({ ...form, flagged_counterparty: e.target.checked })} />
            Alert on interaction with flagged addresses
          </label>
          {formError ? <p className="text-xs text-red-600">{formError}</p> : null}
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" size="sm" onClick={() => setMonitorModal(false)}>Cancel</Button>
            <Button size="sm" onClick={submitMonitor} disabled={createMonitor.isPending}>
              {createMonitor.isPending ? <Spinner className="border-white/40" /> : null} Create rule
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
