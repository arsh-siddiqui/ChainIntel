import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Route, Search, ShieldAlert } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button, Card, CardHeader, Input, Select, Spinner, Badge, Skeleton, EmptyState } from "@/components/common/ui";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { GRAPH_NODE_COLORS } from "@/lib/constants";
import { formatCrypto, truncateMiddle } from "@/lib/formatters";
import type { GraphData, TraceResult } from "@/types";

const NODE_TYPES = ["victim", "wallet", "ransomware", "scam", "exchange", "mixer", "intermediate", "aggregator", "unknown"] as const;

function GraphInner() {
  const searchParams = useSearchParams();
  const addressParam = searchParams.get("address") ?? "0x12d6621e19a95080e0276664261065623b1a0623";
  const [source, setSource] = useState(addressParam);
  const [appliedSource, setAppliedSource] = useState(addressParam);
  const [hops, setHops] = useState(3);
  const [showAmounts, setShowAmounts] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const [trace, setTrace] = useState<TraceResult | null>(null);
  const [traceForm, setTraceForm] = useState({ target: "", direction: "outgoing", max_hops: 4 });

  useEffect(() => {
    if (addressParam) {
      setSource(addressParam);
      setAppliedSource(addressParam);
    }
  }, [addressParam]);

  const { data: graph, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["graph", appliedSource, hops],
    queryFn: async () => (await api.get<GraphData>(`/wallets/${encodeURIComponent(appliedSource)}/graph?hops=${hops}&max_nodes=200`)).data,
    enabled: appliedSource.length >= 4,
  });

  const traceMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<TraceResult>("/graph/trace", {
          wallet_address: appliedSource,
          direction: traceForm.direction,
          target_address: traceForm.target || undefined,
          max_hops: traceForm.max_hops,
        })
      ).data,
    onSuccess: (result) => {
      setTrace(result);
      if (result.found === false) toast.message("Target not reachable", { description: result.note });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Trace failed"),
  });

  const toggleType = (type: string) => {
    setHiddenTypes((current) => {
      const next = new Set(current);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const stats = graph?.stats;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="font-heading text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">Link Analysis & Multi-Hop Attribution Graph</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Interactive transaction graph with bounded-hop fund-flow tracing.</p>
        </div>
        {stats ? (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Badge>{stats.node_count} nodes</Badge>
            <Badge>{stats.edge_count} edges</Badge>
            <Badge>{formatCrypto(stats.total_amount, "BTC")} total</Badge>
            {stats.truncated ? <Badge className="bg-amber-50 text-amber-700 border-amber-200">Truncated (node cap)</Badge> : null}
          </div>
        ) : null}
      </div>

      <Card className="p-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <form
            className="relative md:flex-1"
            onSubmit={(event) => {
              event.preventDefault();
              setTrace(null);
              setAppliedSource(source.trim());
            }}
          >
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input value={source} onChange={(e) => setSource(e.target.value)} placeholder="Focus wallet address (e.g. 1A1zP1... or 0x...)" className="pl-8 font-mono" aria-label="Focus wallet address" />
          </form>
          <label className="flex items-center gap-1.5 text-xs text-slate-600">
            Max hops
            <Select value={hops} onChange={(e) => setHops(Number(e.target.value))} className="w-20 py-1.5" aria-label="Maximum hops">
              {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </Select>
          </label>
          <label className="flex items-center gap-1.5 text-xs text-slate-600">
            <input type="checkbox" checked={showAmounts} onChange={(e) => setShowAmounts(e.target.checked)} /> Amounts
          </label>
          <label className="flex items-center gap-1.5 text-xs text-slate-600">
            <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} /> Labels
          </label>
          <Button type="button" onClick={() => { setTrace(null); setAppliedSource(source.trim()); }} disabled={isFetching || source.trim().length < 4}>
            {isFetching ? <Spinner className="border-white/40" /> : <Search size={14} />} Load graph
          </Button>
        </div>

        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-2.5 dark:border-slate-800">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium text-slate-400">Node types:</span>
            {NODE_TYPES.map((type) => {
              const palette = GRAPH_NODE_COLORS[type];
              const hidden = hiddenTypes.has(type);
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleType(type)}
                  aria-pressed={!hidden}
                  className={`rounded-md border px-2 py-0.5 text-[10px] font-medium transition-opacity ${hidden ? "opacity-35" : ""}`}
                  style={{ borderColor: palette.border, color: palette.text, background: palette.bg }}
                >
                  {palette.label}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
            <span className="font-mono text-[10px] font-bold uppercase text-slate-500">Presets:</span>
            <button
              type="button"
              onClick={() => {
                const a = "0x12d6621e19a95080e0276664261065623b1a0623";
                setSource(a);
                setAppliedSource(a);
                setTrace(null);
              }}
              className="rounded border border-purple-200 bg-purple-50 px-2 py-0.5 font-mono text-[10px] font-bold text-purple-700 hover:bg-purple-100 dark:border-purple-900 dark:bg-purple-950/80 dark:text-purple-300 transition-colors"
            >
              Tornado Cash Mixer
            </button>
            <button
              type="button"
              onClick={() => {
                const a = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa";
                setSource(a);
                setAppliedSource(a);
                setTrace(null);
              }}
              className="rounded border border-amber-200 bg-amber-50 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-800 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950/80 dark:text-amber-300 transition-colors"
            >
              Satoshi Genesis
            </button>
            <button
              type="button"
              onClick={() => {
                const a = "0x098b716b8aaf21512996dc57eb0615e2383e2f96";
                setSource(a);
                setAppliedSource(a);
                setTrace(null);
              }}
              className="rounded border border-rose-200 bg-rose-50 px-2 py-0.5 font-mono text-[10px] font-bold text-rose-700 hover:bg-rose-100 dark:border-rose-900 dark:bg-rose-950/80 dark:text-rose-300 transition-colors"
            >
              Ronin Hack ($620M)
            </button>
            <button
              type="button"
              onClick={() => {
                const a = "19R2w9h5dK1i9fG3XjP4s6d9L2k1N3m4P";
                setSource(a);
                setAppliedSource(a);
                setTrace(null);
              }}
              className="rounded border border-red-200 bg-red-50 px-2 py-0.5 font-mono text-[10px] font-bold text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950/80 dark:text-red-300 transition-colors"
            >
              WannaCry Ransomware
            </button>
            <button
              type="button"
              onClick={() => {
                const a = "0x28c6c06298d514db089934071355e5743bf21d60";
                setSource(a);
                setAppliedSource(a);
                setTrace(null);
              }}
              className="rounded border border-teal-200 bg-teal-50 px-2 py-0.5 font-mono text-[10px] font-bold text-teal-700 hover:bg-teal-100 dark:border-teal-900 dark:bg-teal-950/80 dark:text-teal-300 transition-colors"
            >
              Binance Hot Wallet
            </button>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-4">
        <div className="space-y-4 xl:col-span-3">
          {isError ? (
            <Card>
              <EmptyState title="Graph unavailable" description={(error as Error).message} action={<Button size="sm" variant="secondary" onClick={() => void refetch()}>Retry</Button>} />
            </Card>
          ) : isLoading || !graph ? (
            <Card className="flex h-[620px] items-center justify-center p-6">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Spinner /> Building transaction graph…
              </div>
            </Card>
          ) : graph.nodes.length === 0 ? (
            <Card>
              <EmptyState title="No graph data" description="No indexed transactions found for this wallet." />
            </Card>
          ) : (
            <GraphCanvas
              graph={graph}
              trace={trace}
              showAmounts={showAmounts}
              showLabels={showLabels}
              hiddenTypes={hiddenTypes}
              minHeight={620}
              onSetFocus={(addr) => {
                setSource(addr);
                setAppliedSource(addr);
                setTrace(null);
              }}
              onTraceFromHere={(addr) => {
                setTraceForm((prev) => ({ ...prev, target: addr }));
              }}
            />
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader title="Fund-flow trace" subtitle="Bounded path search over the indexed graph" />
            <div className="space-y-3 p-4">
              <div>
                <label className="text-xs font-medium text-slate-600" htmlFor="trace-target">Destination wallet</label>
                <Input id="trace-target" value={traceForm.target} onChange={(e) => setTraceForm({ ...traceForm, target: e.target.value })} placeholder="Target address (optional)" className="mt-1 font-mono text-xs" />
              </div>
              <div className="flex gap-2">
                <label className="flex-1 text-xs font-medium text-slate-600">
                  Direction
                  <Select value={traceForm.direction} onChange={(e) => setTraceForm({ ...traceForm, direction: e.target.value })} className="mt-1 w-full py-1.5 text-xs">
                    <option value="outgoing">Outgoing (downstream)</option>
                    <option value="incoming">Incoming (upstream)</option>
                  </Select>
                </label>
                <label className="w-24 text-xs font-medium text-slate-600">
                  Max hops
                  <Select value={traceForm.max_hops} onChange={(e) => setTraceForm({ ...traceForm, max_hops: Number(e.target.value) })} className="mt-1 w-full py-1.5 text-xs">
                    {[1, 2, 3, 4, 5, 6, 7].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </Select>
                </label>
              </div>
              <Button size="sm" className="w-full" disabled={traceMutation.isPending || appliedSource.length < 4} onClick={() => traceMutation.mutate()}>
                {traceMutation.isPending ? <Spinner className="border-white/40" /> : <Route size={13} />} Trace funds
              </Button>
              <p className="text-[10px] leading-relaxed text-slate-400">
                The result is the shortest observed path in the available transaction graph — not a claim about the true flow of illicit funds.
              </p>
            </div>
          </Card>

          {trace ? (
            <Card>
              <CardHeader
                title="Trace result"
                subtitle={trace.found === false ? "Target not reachable" : trace.path ? `${trace.hops} hops · ${formatCrypto(trace.total_amount ?? 0, "BTC")} bounded flow` : `${trace.levels?.length ?? 0} hop levels explored`}
              />
              <div className="space-y-3 p-4">
                {trace.path && trace.path.length > 0 ? (
                  <>
                    <ol className="space-y-1">
                      {trace.path.map((address, index) => (
                        <li key={address} className="flex items-center gap-2 text-xs">
                          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary-50 text-[9px] font-bold text-primary">{index}</span>
                          <span className="font-mono text-[11px] text-ink">{truncateMiddle(address, 14, 6)}</span>
                          {trace.suspicious_nodes.some((s) => s.address === address) ? (
                            <Badge className="bg-red-50 text-red-700 border-red-200" title="Wallet matches configured threat datasets">
                              <ShieldAlert size={10} /> flagged
                            </Badge>
                          ) : null}
                        </li>
                      ))}
                    </ol>
                    {trace.paths && trace.paths.length > 1 ? (
                      <div>
                        <p className="text-[11px] font-semibold text-slate-500">Alternative paths found: {trace.paths.length}</p>
                        <ul className="mt-1 space-y-0.5">
                          {trace.paths.slice(1).map((p, index) => (
                            <li key={index} className="text-[10px] text-slate-400">
                              {p.hops} hops · {formatCrypto(p.amount, "BTC")}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </>
                ) : null}
                {trace.levels && trace.levels.length > 0 ? (
                  <ol className="space-y-1.5">
                    {trace.levels.map((level) => (
                      <li key={level.hop} className="text-xs">
                        <span className="font-semibold text-slate-500">Hop {level.hop}</span>
                        <div className="mt-0.5 flex flex-wrap gap-1">
                          {level.addresses.map((entry) => (
                            <span key={entry.address} className={`rounded border px-1.5 py-0.5 font-mono text-[10px] ${entry.suspicious ? "border-red-200 bg-red-50 text-red-700" : "border-slate-200 bg-white text-slate-600"}`} title={entry.address}>
                              {truncateMiddle(entry.address, 10, 4)}
                            </span>
                          ))}
                        </div>
                      </li>
                    ))}
                  </ol>
                ) : null}
                {trace.suspicious_nodes.length > 0 ? (
                  <div className="rounded-lg border border-red-100 bg-red-50/60 p-2.5">
                    <p className="text-[11px] font-semibold text-red-700">Flagged nodes in explored subgraph</p>
                    <ul className="mt-1 space-y-1">
                      {trace.suspicious_nodes.map((node) => (
                        <li key={node.address} className="text-[10px] text-red-600">
                          <span className="font-mono">{truncateMiddle(node.address, 12, 6)}</span> — {node.categories.join(", ")} ({node.sources[0]})
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                <div className="flex items-center justify-between">
                  <Badge className="bg-slate-100 text-slate-500 border-slate-200">{trace.nodes_explored} wallets explored</Badge>
                  <Button size="sm" variant="ghost" onClick={() => setTrace(null)}>
                    Clear
                  </Button>
                </div>
              </div>
            </Card>
          ) : null}

          <Card>
            <CardHeader title="Graph metrics" />
            <div className="p-4">
              {stats ? (
                <dl className="space-y-2 text-sm">
                  {[
                    ["Total hops", String(stats.hops)],
                    ["Unique wallets", String(stats.unique_wallets)],
                    ["Transaction edges", String(stats.edge_count)],
                    ["Total observed amount", formatCrypto(stats.total_amount, "BTC")],
                    ["Focus", truncateMiddle(graph.focus_address, 12, 6)],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                      <dt className="text-xs text-slate-500">{label}</dt>
                      <dd className="font-mono text-xs font-medium text-ink">{value}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <Skeleton className="h-24 w-full" />
              )}
            </div>
          </Card>

          <Card className="p-4">
            <p className="flex items-center gap-1.5 text-[11px] text-slate-400">
              Graph edges aggregate parallel transactions; node colors encode type and threat risk.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function GraphPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs font-mono text-slate-400">Loading Graph Engine…</div>}>
      <GraphInner />
    </Suspense>
  );
}
