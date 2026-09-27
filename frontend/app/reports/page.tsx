"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Download, FileText, Plus } from "lucide-react";
import { api, apiDownload } from "@/lib/api";
import { Button, Card, CardHeader, Input, Spinner, Badge, Skeleton, EmptyState } from "@/components/common/ui";
import { Modal } from "@/components/common/modal";
import { RiskBadge } from "@/components/common/risk-badge";
import { formatDateTime, formatCrypto, truncateMiddle } from "@/lib/formatters";
import type { ReportSummary, PageMeta } from "@/types";

function ReportsInner() {
  const searchParams = useSearchParams();
  const [selectedId, setSelectedId] = useState(searchParams.get("report") ?? "");
  const [generateModal, setGenerateModal] = useState(false);
  const [walletInput, setWalletInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: async () => {
      const response = await api.get<ReportSummary[]>("/reports?page=1&page_size=50");
      return { rows: response.data, meta: response.meta as unknown as PageMeta };
    },
  });

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ["report", selectedId],
    queryFn: async () => (await api.get<ReportSummary>(`/reports/${selectedId}`)).data,
    enabled: selectedId.length > 4,
  });

  const rows = data?.rows ?? [];
  const activeReport = report ?? rows.find((r) => r.id === selectedId);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">Reports</h2>
          <p className="text-xs text-slate-500">Forensic investigation reports with transparent indicators and embedded disclaimers.</p>
        </div>
        <Button onClick={() => setGenerateModal(true)}>
          <Plus size={14} /> Generate Report
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Generated reports" subtitle="Select a report to preview" />
          {isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <EmptyState title="No reports yet" description="Generate one from a case or directly from a wallet address." />
          ) : (
            <ul className="thin-scroll max-h-[480px] divide-y divide-slate-100 overflow-y-auto">
              {rows.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(item.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-slate-50 ${selectedId === item.id ? "bg-primary-50/60" : ""}`}
                  >
                    <p className="truncate text-xs font-medium text-ink">{item.title}</p>
                    <p className="mt-0.5 text-[10px] text-slate-400">
                      {truncateMiddle(item.wallet_address, 12, 6)} · {formatDateTime(item.created_at)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="lg:col-span-2">
          {reportLoading && selectedId ? (
            <Card className="p-6">
              <Skeleton className="h-6 w-64" />
              <Skeleton className="mt-4 h-40 w-full" />
            </Card>
          ) : activeReport ? (
            <ReportPreview report={activeReport} />
          ) : (
            <Card>
              <EmptyState icon={<FileText size={32} />} title="Select a report" description="Choose a report on the left to preview its sections." />
            </Card>
          )}
        </div>
      </div>

      <Modal open={generateModal} onClose={() => setGenerateModal(false)} title="Generate investigation report">
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600" htmlFor="report-wallet">Wallet address</label>
            <Input id="report-wallet" value={walletInput} onChange={(e) => setWalletInput(e.target.value)} placeholder="e.g. 1A1zP1... or 0x..." className="mt-1 font-mono text-xs" />
            <p className="mt-1 text-[10px] text-slate-400">The wallet must have at least one investigation (it runs automatically if needed via a case link).</p>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" size="sm" onClick={() => setGenerateModal(false)}>Cancel</Button>
            <Button
              size="sm"
              disabled={walletInput.trim().length < 4}
              onClick={async () => {
                const response = await api.post<{ id: string }>("/reports/generate", { wallet_address: walletInput.trim() });
                setGenerateModal(false);
                setSelectedId(response.data.id);
                void data; // list refreshes via invalidation below
                window.location.reload();
              }}
            >
              Generate
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function ReportPreview({ report }: { report: ReportSummary }) {
  const payload = report.payload;
  if (!payload) {
    return (
      <Card className="p-6">
        <p className="text-sm text-slate-500">Loading full report payload…</p>
      </Card>
    );
  }
  const wallet = payload.wallet_summary;
  const risk = payload.risk;

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 bg-gradient-to-b from-white to-slate-50 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-lg font-bold text-ink">ChainIntel</p>
            <p className="text-xs font-medium text-slate-500">Blockchain OSINT Investigation Report</p>
          </div>
          <div className="text-right text-[11px] text-slate-500">
            <p>{payload.case ? `${payload.case.case_number} — ${payload.case.title}` : "No linked case"}</p>
            <p>Generated: {formatDateTime(payload.generated_at)}</p>
          </div>
        </div>
      </div>

      <div className="space-y-5 p-6">
        <Section n={1} title="Executive Summary">
          <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
            <Metric label="Wallet" value={truncateMiddle(wallet.address ?? payload.wallet, 12, 6)} mono />
            <Metric label="Blockchain" value={payload.blockchain} />
            <Metric label="Balance" value={formatCrypto(wallet.balance ?? 0, wallet.asset ?? "")} mono />
            <Metric label="Status" value={payload.status} />
            <Metric label="Threat findings" value={String(payload.threat_findings.length)} />
            <Metric label="OSINT (FOUND)" value={String(payload.osint_findings.filter((o) => o.status === "FOUND").length)} />
            <Metric label="Risk score" value={`${risk.score}/${risk.max_score}`} />
            <div>
              <p className="text-[10px] font-medium text-slate-400">Risk band</p>
              <div className="mt-0.5">
                <RiskBadge band={risk.band} />
              </div>
            </div>
          </div>
        </Section>

        <Section n={2} title="Wallet Information">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs md:grid-cols-3">
            {Object.entries(wallet)
              .filter(([, value]) => value !== null && value !== undefined)
              .slice(0, 12)
              .map(([key, value]) => (
                <div key={key} className="flex justify-between gap-2 border-b border-slate-50 pb-1">
                  <dt className="text-slate-400">{key.replace(/_/g, " ")}</dt>
                  <dd className="truncate font-medium text-ink">{String(value)}</dd>
                </div>
              ))}
          </dl>
        </Section>

        <Section n={3} title={`Transaction Summary (${payload.transactions.length})`}>
          <div className="thin-scroll max-h-56 overflow-y-auto rounded-lg border border-slate-100">
            <table className="w-full text-[11px]">
              <thead className="sticky top-0 bg-slate-50">
                <tr className="text-left text-slate-400">
                  <th className="px-3 py-1.5 font-medium">Hash</th>
                  <th className="px-3 py-1.5 font-medium">From</th>
                  <th className="px-3 py-1.5 font-medium">To</th>
                  <th className="px-3 py-1.5 text-right font-medium">Amount</th>
                  <th className="px-3 py-1.5 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {payload.transactions.slice(0, 20).map((tx) => (
                  <tr key={tx.tx_hash}>
                    <td className="px-3 py-1 font-mono">{truncateMiddle(tx.tx_hash, 10, 4)}</td>
                    <td className="px-3 py-1 font-mono text-slate-500">{truncateMiddle(tx.from_address ?? "—", 8, 4)}</td>
                    <td className="px-3 py-1 font-mono text-slate-500">{truncateMiddle(tx.to_address ?? "—", 8, 4)}</td>
                    <td className="px-3 py-1 text-right font-mono">{formatCrypto(tx.amount, tx.asset)}</td>
                    <td className="px-3 py-1 text-slate-400">{formatDateTime(tx.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section n={4} title="Threat Intelligence">
          {payload.threat_findings.length === 0 ? (
            <p className="text-xs text-slate-400">No threat-intelligence matches.</p>
          ) : (
            <ul className="space-y-1.5">
              {payload.threat_findings.map((threat, index) => (
                <li key={index} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 px-3 py-2 text-xs">
                  <span>
                    <Badge className="bg-red-50 text-red-700 border-red-200">{threat.category}</Badge> <span className="ml-1 font-medium text-ink">{threat.label}</span>
                  </span>
                  <span className="text-[10px] text-slate-400">{threat.source} · {Math.round(threat.confidence * 100)}%</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section n={5} title="OSINT Correlation">
          <ul className="space-y-1.5">
            {payload.osint_findings.filter((o) => o.status === "FOUND").length === 0 ? (
              <p className="text-xs text-slate-400">No automated OSINT findings.</p>
            ) : (
              payload.osint_findings
                .filter((o) => o.status === "FOUND")
                .map((finding, index) => (
                  <li key={index} className="rounded-lg border border-slate-100 px-3 py-2 text-xs">
                    <span className="font-medium text-ink">{finding.source_name}</span>
                    <p className="mt-0.5 text-[11px] text-slate-500">{finding.finding}</p>
                  </li>
                ))
            )}
          </ul>
        </Section>

        <Section n={6} title="Fund Flow">
          {payload.fund_flow.path && payload.fund_flow.path.length > 0 ? (
            <div>
              <p className="break-all font-mono text-[11px] text-ink">{payload.fund_flow.path.join(" → ")}</p>
              <p className="mt-1 text-[11px] text-slate-500">
                Hops: {payload.fund_flow.hops} · Bounded flow: {formatCrypto(payload.fund_flow.total_amount ?? 0, "BTC")}
              </p>
              <p className="mt-1 text-[10px] text-amber-700">{payload.fund_flow.disclaimer}</p>
            </div>
          ) : (
            <p className="text-xs text-slate-400">No bounded fund-flow path computed.</p>
          )}
        </Section>

        <Section n={7} title="Risk Indicators">
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-slate-100 text-left text-slate-400">
                <th className="py-1 font-medium">Indicator</th>
                <th className="py-1 font-medium">Status</th>
                <th className="py-1 text-right font-medium">Weight</th>
                <th className="py-1 font-medium">Evidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {risk.indicators.map((indicator) => (
                <tr key={indicator.name}>
                  <td className="py-1.5 font-medium text-ink">{indicator.name}</td>
                  <td className="py-1.5">
                    <span className={indicator.status === "TRIGGERED" ? "text-red-600 font-semibold" : "text-emerald-600"}>{indicator.status === "TRIGGERED" ? "Triggered" : "—"}</span>
                  </td>
                  <td className="py-1.5 text-right font-mono">+{indicator.weight}</td>
                  <td className="py-1.5 text-slate-500">{indicator.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[10px] text-slate-400">{risk.disclaimer}</p>
        </Section>

        <Section n={8} title="Evidence">
          {payload.evidence.length === 0 ? (
            <p className="text-xs text-slate-400">No evidence records attached to this case.</p>
          ) : (
            <ul className="space-y-1 text-xs">
              {payload.evidence.map((item) => (
                <li key={item.id} className="flex items-center justify-between border-b border-slate-50 py-1">
                  <span className="font-medium text-ink">{item.title}</span>
                  <span className="font-mono text-[10px] text-slate-400">{item.sha256?.slice(0, 20)}…</span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section n={9} title="Timeline">
          {payload.timeline.length === 0 ? (
            <p className="text-xs text-slate-400">No case timeline.</p>
          ) : (
            <ol className="space-y-1 text-xs">
              {payload.timeline.slice(0, 12).map((event) => (
                <li key={event.id} className="flex gap-2">
                  <span className="shrink-0 text-slate-400">{formatDateTime(event.created_at)}</span>
                  <span className="text-slate-600">{event.description}</span>
                </li>
              ))}
            </ol>
          )}
        </Section>

        <Section n={10} title="Analyst Notes">
          <p className="whitespace-pre-wrap text-xs text-slate-600">{payload.analyst_notes || "No analyst notes recorded."}</p>
        </Section>

        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
          <p className="text-[11px] font-medium text-amber-800">Important Notice</p>
          {payload.disclaimers.map((disclaimer) => (
            <p key={disclaimer} className="mt-1 text-[11px] text-amber-700">
              • {disclaimer}
            </p>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          <Button size="sm" onClick={() => apiDownload(`/reports/${report.id}/download?format=pdf`, `${report.id}.pdf`)}>
            <Download size={13} /> Generate PDF
          </Button>
          <Button size="sm" variant="secondary" onClick={() => apiDownload(`/reports/${report.id}/download?format=json`, `${report.id}.json`)}>
            <Download size={13} /> Download JSON
          </Button>
          <Button size="sm" variant="secondary" onClick={() => apiDownload(`/reports/${report.id}/download?format=csv`, `${report.id}.csv`)}>
            <Download size={13} /> Export CSV
          </Button>
        </div>
      </div>
    </Card>
  );
}

function Section({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="flex h-5 w-5 items-center justify-center rounded-md bg-primary-50 text-[10px] font-bold text-primary">{n}</span>
        {title}
      </h3>
      {children}
    </section>
  );
}

function Metric({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-2.5 py-1.5">
      <p className="text-[10px] font-medium text-slate-400">{label}</p>
      <p className={`truncate text-xs font-semibold text-ink ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<Card className="p-6"><Spinner /> Loading…</Card>}>
      <ReportsInner />
    </Suspense>
  );
}
