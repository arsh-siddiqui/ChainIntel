"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, CircleSlash, Database, Server, Timer } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardHeader, Badge, Skeleton } from "@/components/common/ui";
import type { OSINTSourceStatus, ProviderStatus } from "@/types";

interface ProvidersData {
  mode: string;
  blockchain_providers: ProviderStatus[];
  osint_sources: OSINTSourceStatus[];
  osint_provider_enabled: boolean;
  note: string;
}

interface OverviewData {
  app_name: string;
  app_version: string;
  mode: string;
  database: { engine: string; url: string };
  monitoring: { enabled: boolean; poll_interval_seconds: number; active_monitors: number; alerts_total: number };
  limits: { rate_limit_requests: number; rate_limit_window_seconds: number; max_upload_mb: number };
  evidence_dir: string;
  cors_origins: string[];
}

export default function SettingsPage() {
  const { data: providers, isLoading: providersLoading } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => (await api.get<ProvidersData>("/settings/providers")).data,
  });

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ["overview"],
    queryFn: async () => (await api.get<OverviewData>("/settings/overview")).data,
  });

  const statusBadge = (status: string) =>
    status === "CONFIGURED" ? (
      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">
        <CheckCircle2 size={11} /> Configured
      </Badge>
    ) : (
      <Badge className="bg-amber-50 text-amber-700 border-amber-200">
        <CircleSlash size={11} /> Not Configured
      </Badge>
    );

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink">Settings</h2>
        <p className="text-xs text-slate-500">Provider configuration status and system limits. Secret values are never displayed.</p>
      </div>

      <Card>
        <CardHeader title="Blockchain Providers" subtitle="Real-time data sources for wallet and transaction retrieval" />
        <div className="grid gap-3 p-5 md:grid-cols-2">
          {providersLoading
            ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)
            : (providers?.blockchain_providers ?? []).map((provider) => (
                <div key={provider.blockchain + provider.name} className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-ink">{provider.name}</p>
                    <p className="text-[11px] capitalize text-slate-400">{provider.blockchain} chain</p>
                  </div>
                  {statusBadge(provider.status)}
                </div>
              ))}
        </div>
        <div className="border-t border-slate-100 bg-slate-50 px-5 py-2.5">
          <p className="text-[11px] text-slate-500">{providers?.note}</p>
        </div>
      </Card>

      <Card>
        <CardHeader title="OSINT Sources" subtitle="Link-only public sources and restricted analyst records" />
        <div className="grid gap-2 p-5 md:grid-cols-2 lg:grid-cols-4">
          {(providers?.osint_sources ?? []).map((source) => (
            <div key={source.name} className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2">
              <span className="truncate text-xs font-medium text-ink">{source.name}</span>
              <Badge className="bg-slate-100 text-slate-600 border-slate-200">Link-only</Badge>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Monitoring" subtitle="Background polling engine configuration" />
        <div className="grid gap-3 p-5 md:grid-cols-4">
          {overviewLoading || !overview ? (
            Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)
          ) : (
            <>
              <InfoTile icon={Timer} label="Poll interval" value={`${overview.monitoring.poll_interval_seconds}s`} />
              <InfoTile icon={CheckCircle2} label="Engine" value={overview.monitoring.enabled ? "Enabled" : "Disabled"} />
              <InfoTile icon={Server} label="Active monitors" value={String(overview.monitoring.active_monitors)} />
              <InfoTile icon={Database} label="Alerts stored" value={String(overview.monitoring.alerts_total)} />
            </>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader title="System" subtitle="Runtime configuration (values redacted where sensitive)" />
        {overviewLoading || !overview ? (
          <div className="p-5">
            <Skeleton className="h-24 w-full" />
          </div>
        ) : (
          <dl className="grid grid-cols-1 gap-x-8 gap-y-2 p-5 text-xs md:grid-cols-2">
            {[
              ["Application", `${overview.app_name} v${overview.app_version}`],
              ["Mode", overview.mode],
              ["Database engine", overview.database.engine],
              ["Database URL", overview.database.url],
              ["Rate limit", `${overview.limits.rate_limit_requests} requests / ${overview.limits.rate_limit_window_seconds}s window`],
              ["Max upload size", `${overview.limits.max_upload_mb} MB`],
              ["Evidence directory", overview.evidence_dir],
              ["CORS origins", overview.cors_origins.join(", ")],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between border-b border-slate-100 py-1.5">
                <dt className="text-slate-500">{label}</dt>
                <dd className="font-mono text-[11px] text-ink">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </Card>
    </div>
  );
}

function InfoTile({ icon: Icon, label, value }: { icon: typeof Timer; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-100 px-4 py-3">
      <div className="flex items-center gap-2 text-slate-400">
        <Icon size={14} />
        <p className="text-[11px] font-medium">{label}</p>
      </div>
      <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}
