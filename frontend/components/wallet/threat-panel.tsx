"use client";

import { ExternalLink } from "lucide-react";
import type { ThreatFinding } from "@/types";
import { Card, CardHeader, Badge, EmptyState } from "@/components/common/ui";
import { confidencePercent, formatDateTime } from "@/lib/formatters";

const CATEGORY_STYLES: Record<string, string> = {
  Ransomware: "bg-red-50 text-red-700 border-red-200",
  Scam: "bg-orange-50 text-orange-700 border-orange-200",
  Phishing: "bg-amber-50 text-amber-700 border-amber-200",
  Blacklist: "bg-red-50 text-red-700 border-red-200",
  Fraud: "bg-orange-50 text-orange-700 border-orange-200",
  Exploit: "bg-red-50 text-red-700 border-red-200",
  "Suspicious Service": "bg-purple-50 text-purple-700 border-purple-200",
  Unknown: "bg-slate-100 text-slate-600 border-slate-200",
};

export function ThreatPanel({ walletThreats, counterpartyThreats }: { walletThreats: ThreatFinding[]; counterpartyThreats: ThreatFinding[] }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader title="Threat intelligence matches" subtitle="Records from configured threat datasets — source always shown" />
        {walletThreats.length === 0 ? (
          <EmptyState title="No threat-intelligence matches" description="This wallet does not appear in any configured threat dataset. Absence of a match is not proof of safety." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {walletThreats.map((threat, index) => (
              <li key={`${threat.wallet_address}-${threat.source}-${index}`} className="px-5 py-3.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge className={CATEGORY_STYLES[threat.category] ?? CATEGORY_STYLES.Unknown}>{threat.category}</Badge>
                    <span className="text-sm font-medium text-ink">{threat.label}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span title="Source-reported confidence">{confidencePercent(threat.confidence)} confidence</span>
                    <Badge className="bg-slate-100 text-slate-600 border-slate-200">{threat.status ?? "IMPORTED"}</Badge>
                  </div>
                </div>
                <dl className="mt-2 grid grid-cols-1 gap-x-6 gap-y-1 text-[11px] text-slate-500 sm:grid-cols-3">
                  <div>
                    <dt className="inline font-medium text-slate-400">Source: </dt>
                    <dd className="inline">{threat.source}</dd>
                  </div>
                  <div>
                    <dt className="inline font-medium text-slate-400">First seen: </dt>
                    <dd className="inline">{formatDateTime(threat.first_seen)}</dd>
                  </div>
                  <div>
                    <dt className="inline font-medium text-slate-400">Last seen: </dt>
                    <dd className="inline">{formatDateTime(threat.last_seen)}</dd>
                  </div>
                </dl>
                {threat.notes ? <p className="mt-1.5 text-xs text-slate-600">{threat.notes}</p> : null}
                {threat.reference_url ? (
                  <a href={threat.reference_url} target="_blank" rel="noopener noreferrer" className="mt-1.5 inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
                    <ExternalLink size={11} /> Evidence reference
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <CardHeader title="High-risk counterparties" subtitle="Wallets transacting with the investigated address that carry threat records" />
        {counterpartyThreats.length === 0 ? (
          <EmptyState title="No flagged counterparties" description="None of the observed counterparties match configured threat datasets." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {counterpartyThreats.map((threat, index) => (
              <li key={`${threat.wallet_address}-${index}`} className="flex flex-wrap items-center justify-between gap-2 px-5 py-2.5">
                <span className="font-mono text-xs text-ink">{threat.wallet_address}</span>
                <div className="flex items-center gap-2">
                  <Badge className={CATEGORY_STYLES[threat.category] ?? CATEGORY_STYLES.Unknown}>{threat.category}</Badge>
                  <span className="text-[11px] text-slate-500">{threat.source}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
