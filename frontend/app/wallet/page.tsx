"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { FileText, FolderLock, GitFork, Search, ShieldCheck } from "lucide-react";
import { api, ApiError, explorerUrl } from "@/lib/api";
import { useInvestigation, PIPELINE_STEPS } from "@/hooks/use-investigation";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, EmptyState } from "@/components/common/ui";
import { CHAIN_OPTIONS, DEMO_TARGET_PRESETS } from "@/lib/constants";
import { WalletOverview } from "@/components/wallet/wallet-overview";
import { ThreatBanner } from "@/components/wallet/threat-banner";
import { RiskPanel } from "@/components/wallet/risk-panel";
import { TxTable } from "@/components/wallet/tx-table";
import { ThreatPanel } from "@/components/wallet/threat-panel";
import { OsintPanel } from "@/components/wallet/osint-panel";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { ActivityChart } from "@/components/charts/charts";
import { formatCrypto, truncateMiddle } from "@/lib/formatters";
import type { CaseDetail, InvestigationBundle, TraceResult } from "@/types";

const TABS = ["Overview", "Transactions", "Graph", "Threat Intelligence", "OSINT", "Analysis", "Notes", "Case"] as const;
type Tab = (typeof TABS)[number];

function ProgressStepper({ step, error }: { step: number; error: string | null }) {
  return (
    <Card className="p-5">
      <p className="text-sm font-semibold text-ink">{error ? "Investigation failed" : "Running investigation pipeline"}</p>
      <ol className="mt-3 space-y-2">
        {PIPELINE_STEPS.map((label, index) => {
          const done = step > index;
          const active = step === index;
          const failed = error !== null && active;
          return (
            <li key={label} className="flex items-center gap-2.5 text-sm">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-bold ${
                  failed
                    ? "border-red-300 bg-red-50 text-red-600"
                    : done
                      ? "border-emerald-200 bg-emerald-50 text-emerald-600"
                      : active
                        ? "border-primary bg-primary-50 text-primary"
                        : "border-slate-200 bg-white text-slate-400"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              <span className={done ? "text-slate-500" : active ? (failed ? "text-red-600 font-medium" : "font-medium text-ink") : "text-slate-400"}>{label}</span>
              {active && !failed && !done ? <Spinner className="ml-1 h-3 w-3" /> : null}
            </li>
          );
        })}
      </ol>
      {error ? <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p> : null}
    </Card>
  );
}

function InvestigateForm({ onSubmit, isLoading, defaultAddress }: { onSubmit: (address: string, chain: string) => void; isLoading: boolean; defaultAddress: string }) {
  const [address, setAddress] = useState(defaultAddress);
  const [chain, setChain] = useState("auto");

  useEffect(() => {
    if (defaultAddress) setAddress(defaultAddress);
  }, [defaultAddress]);

  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(address.trim(), chain);
      }}
    >
      <div className="flex flex-col gap-2.5 md:flex-row">
        <Input
          value={address}
          onChange={(event) => setAddress(event.target.value)}
          placeholder="Enter target wallet address (e.g. 1..., bc1q..., 0x...)"
          aria-label="Wallet address"
          className="font-mono md:flex-1 text-sm"
        />
        <Select
          value={chain}
          onChange={(event) => setChain(event.target.value)}
          aria-label="Blockchain selector"
          className="md:w-56 font-mono text-xs"
        >
          {CHAIN_OPTIONS.map((option) => (
            <option key={option.value} value={option.value} className="bg-white text-slate-800 dark:bg-slate-900 dark:text-slate-100">
              {option.label}
            </option>
          ))}
        </Select>
        <Button
          type="submit"
          disabled={isLoading || address.trim().length < 4}
          className="md:w-44 bg-gradient-to-r from-sky-500 via-blue-600 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 text-white font-bold shadow-lg shadow-cyan-500/25 active:scale-[0.98]"
        >
          {isLoading ? <Spinner className="border-white/40" /> : <Search size={15} className="stroke-[2.5]" />}
          Run Investigation
        </Button>
      </div>

      <div className="pt-1">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="font-mono text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wide mr-1">
            DEMO TARGET PRESETS:
          </span>
          {DEMO_TARGET_PRESETS.map((preset) => (
            <button
              key={preset.address}
              type="button"
              onClick={() => {
                setAddress(preset.address);
                setChain(preset.chain);
                onSubmit(preset.address, preset.chain);
              }}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 py-1 font-mono text-[11px] font-medium text-slate-700 hover:border-sky-500 hover:bg-sky-50 hover:text-sky-700 transition-colors dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-sky-500 dark:hover:bg-sky-950/40"
              title={`Investigate ${preset.label} (${preset.address})`}
            >
              <span>{preset.label}</span>
              <span className="rounded bg-slate-100 px-1 py-0.2 text-[9px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                {preset.badge}
              </span>
            </button>
          ))}
        </div>
      </div>

      <p className="text-[11px] font-mono text-slate-400">
        Direct Blockchain Node verification · Bitcoin (keyless live mempool/UTXO) · Ethereum/BSC (multichain RPC)
      </p>
    </form>
  );
}

function WalletPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const addressParam = searchParams.get("address") ?? "";
  const [activeTab, setActiveTab] = useState<Tab>("Overview");
  const [hops, setHops] = useState(3);
  const [notes, setNotes] = useState("");
  const [traceResult, setTraceResult] = useState<TraceResult | null>(null);
  const [showAmounts, setShowAmounts] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [caseWallet, setCaseWallet] = useState("");

  const { investigate, isLoading, error, result, progressStep } = useInvestigation();
  const { data: cached, isLoading: cachedLoading } = useQuery({
    queryKey: ["wallet", addressParam],
    queryFn: async () => (await api.get<{ validation: { valid: boolean; reason: string }; wallet: unknown; investigation: unknown; bundle: InvestigationBundle | null }>(`/wallets/${encodeURIComponent(addressParam)}`)).data,
    enabled: addressParam.length >= 4,
  });

  const bundle = result ?? cached?.bundle ?? null;

  useEffect(() => {
    if (bundle?.wallet) setNotes("");
  }, [bundle?.investigation_id]); // eslint-disable-line react-hooks/exhaustive-deps

  const { data: graphData } = useQuery({
    queryKey: ["wallet-graph", bundle?.address, hops],
    queryFn: async () => (await api.get<InvestigationBundle["graph"]>(`/wallets/${encodeURIComponent(bundle!.address)}/graph?hops=${hops}`)).data,
    enabled: Boolean(bundle) && activeTab === "Graph",
  });

  const notesMutation = useMutation({
    mutationFn: async (value: string) => api.patch(`/wallets/${encodeURIComponent(bundle!.address)}/notes`, { notes: value }),
    onSuccess: () => {
      toast.success("Investigator notes saved");
      void queryClient.invalidateQueries({ queryKey: ["wallet", bundle?.address] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to save notes"),
  });

  const linkCaseMutation = useMutation({
    mutationFn: async (input: { address: string; caseId: number }) =>
      (await api.post<{ investigation_id: number }>(`/cases/${input.caseId}/investigations`, { wallet_address: input.address })).data,
    onSuccess: () => {
      toast.success("Investigation linked to case");
      router.push("/investigations");
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to link case"),
  });

  const { data: casesList } = useQuery({
    queryKey: ["cases-lite"],
    queryFn: async () => (await api.get<CaseDetail[]>("/cases?page=1&page_size=50")).data,
    enabled: activeTab === "Case",
  });

  const createCaseMutation = useMutation({
    mutationFn: async (address: string) =>
      (
        await api.post<CaseDetail>("/cases", {
          title: `Investigation ${truncateMiddle(address, 10, 6)}`,
          description: `Case created from wallet investigation of ${address}.`,
          priority: (bundle?.risk.band === "HIGH" || bundle?.risk.band === "ELEVATED" ? "HIGH" : "MEDIUM") as string,
        })
      ).data,
    onSuccess: async (created) => {
      await queryClient.fetchQuery({ queryKey: ["created-case"], queryFn: () => created });
      await api.post(`/cases/${created.id}/investigations`, { wallet_address: bundle!.address });
      toast.success(`Case ${created.case_number} created and linked`);
      router.push(`/investigations/${created.id}`);
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to create case"),
  });

  const dayActivity = useMemo(() => {
    if (!bundle) return [];
    const byDay = new Map<string, { incoming: number; outgoing: number; count: number }>();
    for (const tx of bundle.transactions) {
      const day = (tx.timestamp ?? "").slice(0, 10);
      if (!day) continue;
      const entry = byDay.get(day) ?? { incoming: 0, outgoing: 0, count: 0 };
      if (tx.to_address === bundle.address) entry.incoming += tx.amount;
      if (tx.from_address === bundle.address) entry.outgoing += tx.amount;
      entry.count += 1;
      byDay.set(day, entry);
    }
    return [...byDay.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([date, v]) => ({ date, ...v }));
  }, [bundle]);

  const counterparties = useMemo(() => {
    if (!bundle) return [];
    const map = new Map<string, { address: string; sent: number; received: number; txs: number }>();
    for (const tx of bundle.transactions) {
      const other = tx.from_address === bundle.address ? tx.to_address : tx.to_address === bundle.address ? tx.from_address : null;
      if (!other) continue;
      const entry = map.get(other) ?? { address: other, sent: 0, received: 0, txs: 0 };
      if (tx.from_address === bundle.address) entry.sent += tx.amount;
      else entry.received += tx.amount;
      entry.txs += 1;
      map.set(other, entry);
    }
    return [...map.values()].sort((a, b) => b.txs - a.txs);
  }, [bundle]);

  const errorMessage = error instanceof ApiError ? error.message : error ? String(error) : null;

  const runInvestigation = (inputAddress: string, chain: string) => {
    setTraceResult(null);
    router.replace(`/wallet?address=${encodeURIComponent(inputAddress)}`, { scroll: false });
    investigate({ address: inputAddress, blockchain: chain });
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-ink">Wallet Investigation</h2>
          <p className="text-xs text-slate-500">Validate, analyze and trace any Bitcoin, Ethereum or BNB Smart Chain wallet against live blockchain data.</p>
        </div>
      </div>

      <Card className="p-5">
        <InvestigateForm onSubmit={runInvestigation} isLoading={isLoading} defaultAddress={addressParam} />
      </Card>

      {isLoading || (progressStep >= 0 && !bundle) ? <ProgressStepper step={progressStep} error={null} /> : null}
      {!isLoading && errorMessage && progressStep < 0 ? (
        <Card className="border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-700">{errorMessage}</p>
          {error instanceof ApiError && (error.code === "PROVIDER_UNAVAILABLE" || error.code === "REQUIRES_CONFIGURATION" || error.code === "NETWORK_ERROR") ? (
            <div className="mt-2 flex flex-wrap gap-2">
              <Button size="sm" variant="ghost" onClick={() => router.push("/settings")}>
                Check provider settings
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}

      {cachedLoading && !bundle && addressParam ? (
        <Card className="p-6">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Spinner /> Loading cached investigation…
          </div>
        </Card>
      ) : null}

      {!bundle && !isLoading && !errorMessage && !cachedLoading ? (
        <Card>
          <EmptyState
            icon={<ShieldCheck size={36} />}
            title="No investigation loaded"
            description="Enter a wallet address above and press Investigate. Bitcoin works keylessly; Ethereum/BSC need a configured provider key."
          />
        </Card>
      ) : null}

      {bundle ? (
        <>
          <ThreatBanner risk={bundle.risk} threats={bundle.threats} />
          <WalletOverview wallet={bundle.wallet} />

          <div role="tablist" aria-label="Investigation sections" className="relative flex gap-1.5 overflow-x-auto rounded-2xl border p-1.5 transition-colors border-slate-200/90 bg-white/80 dark:border-slate-800/80 dark:bg-slate-950/70 backdrop-blur-xl shadow-md">
            {TABS.map((tab) => {
              const active = activeTab === tab;
              return (
                <button
                  key={tab}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setActiveTab(tab)}
                  className={`relative z-10 flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-xs font-bold tracking-tight transition-colors duration-150 ${
                    active
                      ? "text-sky-700 dark:text-cyan-300"
                      : "text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                  }`}
                >
                  {active && (
                    <motion.span
                      layoutId="activeTabPill"
                      transition={{ type: "spring", stiffness: 450, damping: 35 }}
                      className="absolute inset-0 z-[-1] rounded-xl border border-sky-400/40 bg-sky-50 shadow-sm dark:border-cyan-500/40 dark:bg-cyan-500/15 dark:shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    />
                  )}
                  <span>{tab}</span>
                  {tab === "Threat Intelligence" && bundle.threats.length > 0 ? (
                    <span className="rounded-full bg-rose-500/20 border border-rose-500/40 px-2 py-0.5 text-[10px] font-bold text-rose-600 dark:text-rose-300">
                      {bundle.threats.length}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>

          {activeTab === "Overview" ? (
            <div className="space-y-4">
              {/* Contextual Investigation Actions Bar */}
              <div className="console-panel rounded-lg p-3 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2 font-mono text-xs text-slate-500">
                  <span className="font-bold text-ink">ACTIONS FOR {truncateMiddle(bundle.address, 10, 6)}:</span>
                </div>
                <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                  <Link
                    href={`/graph?address=${encodeURIComponent(bundle.address)}`}
                    className="flex items-center gap-1.5 rounded bg-blue-600 px-3 py-1.5 font-bold text-white hover:bg-blue-700 transition-colors"
                  >
                    <GitFork size={13} />
                    <span>LAUNCH LINK ANALYSIS GRAPH</span>
                  </Link>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => createCaseMutation.mutate(bundle.address)}
                    disabled={createCaseMutation.isPending}
                    className="h-8 font-mono text-xs"
                  >
                    <FolderLock size={13} className="mr-1.5" />
                    <span>{createCaseMutation.isPending ? "CREATING..." : "FILE INCIDENT CASE"}</span>
                  </Button>
                  <Link
                    href={`/reports`}
                    className="flex items-center gap-1.5 rounded border border-slate-200 bg-white px-3 py-1.5 font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200 transition-colors"
                  >
                    <FileText size={13} />
                    <span>EXPORT DOSSIER</span>
                  </Link>
                </div>
              </div>

              {/* Forensic Risk Assessment Checklist */}
              <RiskPanel risk={bundle.risk} />

              {/* Split Pane: Transaction Flow Ledger & Direct Counterparties */}
              <div className="grid gap-4 lg:grid-cols-12">
                <div className="console-panel rounded-lg lg:col-span-7 flex flex-col">
                  <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5 dark:border-slate-800">
                    <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
                      RECENT TRANSACTION FLOW ({bundle.transactions.length})
                    </h3>
                    <button
                      onClick={() => setActiveTab("Transactions")}
                      className="font-mono text-[11px] text-blue-600 hover:underline dark:text-blue-400"
                    >
                      VIEW ALL &rarr;
                    </button>
                  </div>
                  <div className="overflow-x-auto flex-1 max-h-[360px] thin-scroll">
                    <TxTable transactions={bundle.transactions.slice(0, 10)} focusAddress={bundle.address} />
                  </div>
                </div>

                <div className="console-panel rounded-lg lg:col-span-5 flex flex-col">
                  <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5 dark:border-slate-800">
                    <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
                      DIRECT PEER COUNTERPARTIES ({counterparties.length})
                    </h3>
                    <Link
                      href={`/graph?address=${encodeURIComponent(bundle.address)}`}
                      className="font-mono text-[11px] text-blue-600 hover:underline dark:text-blue-400"
                    >
                      MAP ON GRAPH &rarr;
                    </Link>
                  </div>
                  <div className="thin-scroll max-h-[360px] overflow-y-auto flex-1">
                    <table className="w-full text-left font-mono text-xs">
                      <thead className="sticky top-0 border-b bg-slate-50 text-[10px] uppercase text-slate-400 dark:bg-slate-900/90 dark:border-slate-800">
                        <tr>
                          <th className="px-3 py-2">PEER ADDRESS</th>
                          <th className="px-2 py-2 text-right">VOLUME</th>
                          <th className="px-3 py-2 text-right">TXS</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                        {counterparties.map((cp) => (
                          <tr key={cp.address} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                            <td className="px-3 py-2">
                              <button
                                type="button"
                                className="font-mono text-xs font-semibold text-blue-600 hover:underline dark:text-blue-400"
                                onClick={() => runInvestigation(cp.address, "auto")}
                                title={cp.address}
                              >
                                {truncateMiddle(cp.address, 10, 5)}
                              </button>
                            </td>
                            <td className="px-2 py-2 text-right font-mono text-xs font-medium text-ink">
                              {formatCrypto(cp.sent + cp.received, bundle.wallet.asset)}
                            </td>
                            <td className="px-3 py-2 text-right font-mono text-xs text-slate-400">
                              {cp.txs}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Activity Volume Telemetry */}
              {dayActivity.length > 0 && (
                <div className="console-panel rounded-lg p-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
                    <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-ink">
                      HISTORICAL INFLOW / OUTFLOW TELEMETRY
                    </h3>
                  </div>
                  <div className="pt-3">
                    <ActivityChart data={dayActivity} />
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {activeTab === "Transactions" ? (
            <Card>
              <CardHeader
                title={`Transactions (${bundle.transactions.length} observed)`}
                subtitle="Newest first · click a hash for full detail"
                action={bundle.wallet.explorer_url ? <a href={bundle.wallet.explorer_url} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-primary hover:underline">Open explorer</a> : null}
              />
              <TxTable transactions={bundle.transactions} focusAddress={bundle.address} />
            </Card>
          ) : null}

          {activeTab === "Graph" ? (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs text-slate-600">
                  Hops
                  <Select value={hops} onChange={(event) => setHops(Number(event.target.value))} className="w-20 py-1.5" aria-label="Graph depth in hops">
                    {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </Select>
                </label>
                <label className="flex items-center gap-1.5 text-xs text-slate-600">
                  <input type="checkbox" checked={showAmounts} onChange={(e) => setShowAmounts(e.target.checked)} /> Show amounts
                </label>
                <label className="flex items-center gap-1.5 text-xs text-slate-600">
                  <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} /> Show labels
                </label>
                <span className="ml-auto text-[11px] text-slate-400">
                  {graphData ? `${graphData.stats.node_count} nodes · ${graphData.stats.edge_count} edges` : bundle.graph.stats.node_count + " nodes · " + bundle.graph.stats.edge_count + " edges"}
                </span>
              </div>
              <GraphCanvas graph={graphData ?? bundle.graph} trace={traceResult} showAmounts={showAmounts} showLabels={showLabels} minHeight={520} />
            </div>
          ) : null}

          {activeTab === "Threat Intelligence" ? <ThreatPanel walletThreats={bundle.threats} counterpartyThreats={bundle.counterparty_threats} /> : null}

          {activeTab === "OSINT" ? <OsintPanel correlation={bundle.osint} /> : null}

          {activeTab === "Analysis" ? <RiskPanel risk={bundle.risk} /> : null}

          {activeTab === "Notes" ? (
            <Card>
              <CardHeader title="Investigator notes" subtitle="Stored with the latest investigation record" />
              <div className="space-y-3 p-5">
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Analyst observations, hypotheses, next steps…"
                  rows={6}
                  aria-label="Investigator notes"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary focus:outline focus:outline-2 focus:outline-primary-100"
                />
                <div className="flex items-center gap-2">
                  <Button size="sm" disabled={notesMutation.isPending || !notes.trim()} onClick={() => notesMutation.mutate(notes)}>
                    Save notes
                  </Button>
                  {bundle.investigation_id ? <Badge>Investigation #{bundle.investigation_id}</Badge> : null}
                </div>
              </div>
            </Card>
          ) : null}

          {activeTab === "Case" ? (
            <Card>
              <CardHeader title="Investigation case" subtitle="Create a new case from this investigation or link it to an existing one" />
              <div className="space-y-4 p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <Button size="sm" disabled={createCaseMutation.isPending} onClick={() => createCaseMutation.mutate(bundle.address)}>
                    Create case from investigation
                  </Button>
                  {bundle.investigation_id ? <Badge className="bg-blue-50 text-blue-700 border-blue-200">Investigation #{bundle.investigation_id}</Badge> : null}
                  {bundle.risk.band ? <Badge>{bundle.risk.band} risk</Badge> : null}
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600" htmlFor="link-case">
                    Link to existing case
                  </label>
                  <div className="mt-1 flex gap-2">
                    <Select id="link-case" value={caseWallet} onChange={(event) => setCaseWallet(event.target.value)} className="flex-1">
                      <option value="">Select a case…</option>
                      {(casesList ?? []).map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.case_number} — {c.title}
                        </option>
                      ))}
                    </Select>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={!caseWallet || linkCaseMutation.isPending}
                      onClick={() => linkCaseMutation.mutate({ address: bundle.address, caseId: Number(caseWallet) })}
                    >
                      Link
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export default function WalletPage() {
  return (
    <Suspense fallback={<Card className="p-6"><Spinner /> Loading…</Card>}>
      <WalletPageInner />
    </Suspense>
  );
}
