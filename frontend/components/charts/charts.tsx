"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDate } from "@/lib/formatters";

const PALETTE = ["#2563EB", "#14B8A6", "#F59E0B", "#8B5CF6", "#EF4444", "#64748B", "#EC4899", "#0EA5E9"];

const tooltipStyle = {
  borderRadius: "8px",
  backgroundColor: "rgba(15, 23, 42, 0.94)",
  borderColor: "rgba(51, 65, 85, 0.6)",
  color: "#F8FAFC",
  fontSize: "12px",
  padding: "8px 12px",
  boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
};

export function ActivityChart({ data }: { data: { date: string; incoming: number; outgoing: number; count: number }[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[260px] items-center justify-center font-mono text-xs text-slate-400">
        No transaction telemetry recorded in this period.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="in" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#14B8A6" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#14B8A6" stopOpacity={0.0} />
          </linearGradient>
          <linearGradient id="out" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563EB" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#2563EB" stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" strokeOpacity={0.15} vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={(v: string) => (v ? v.slice(5) : "")}
          tick={{ fontSize: 10, fill: "#64748B" }}
          tickLine={false}
          axisLine={{ stroke: "#94A3B8", strokeOpacity: 0.2 }}
          minTickGap={24}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#64748B" }}
          tickLine={false}
          axisLine={false}
          width={44}
        />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => formatDate(String(v))} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: "8px" }} />
        <Area type="monotone" dataKey="incoming" name="Incoming (BTC)" stroke="#14B8A6" fill="url(#in)" strokeWidth={2} />
        <Area type="monotone" dataKey="outgoing" name="Outgoing (BTC)" stroke="#2563EB" fill="url(#out)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function CategoryDonut({ data, nameKey = "category" }: { data: { category?: string; risk_level?: string; count: number }[]; nameKey?: string }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[260px] items-center justify-center font-mono text-xs text-slate-400">
        No threat signatures cataloged.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey={nameKey} innerRadius={55} outerRadius={90} paddingAngle={2} strokeWidth={1}>
          {data.map((_, index) => (
            <Cell key={index} fill={PALETTE[index % PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: "6px" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function RiskBar({ data }: { data: { risk_level: string; count: number }[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[260px] items-center justify-center font-mono text-xs text-slate-400">
        No risk distribution profiles recorded.
      </div>
    );
  }

  const colors: Record<string, string> = { LOW: "#10B981", MODERATE: "#F59E0B", ELEVATED: "#F97316", HIGH: "#EF4444" };
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" strokeOpacity={0.15} vertical={false} />
        <XAxis
          dataKey="risk_level"
          tick={{ fontSize: 11, fill: "#64748B", fontWeight: 600 }}
          tickLine={false}
          axisLine={{ stroke: "#94A3B8", strokeOpacity: 0.2 }}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 10, fill: "#64748B" }}
          tickLine={false}
          axisLine={false}
          width={32}
        />
        <Tooltip contentStyle={tooltipStyle} />
        <Bar dataKey="count" name="Investigations" radius={[6, 6, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.risk_level} fill={colors[entry.risk_level] ?? "#94A3B8"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CounterpartyBars({ data }: { data: { address: string; transactions: number; volume: number }[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-[260px] items-center justify-center font-mono text-xs text-slate-400">
        No flagged counterparty volume detected.
      </div>
    );
  }

  const rows = data.map((d) => ({ ...d, short: `${d.address.slice(0, 12)}…` }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#94A3B8" strokeOpacity={0.15} horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 10, fill: "#64748B" }}
          tickLine={false}
          axisLine={{ stroke: "#94A3B8", strokeOpacity: 0.2 }}
        />
        <YAxis
          type="category"
          dataKey="short"
          width={100}
          tick={{ fontSize: 10, fill: "#64748B", fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [value, name === "transactions" ? "Transactions" : name]} />
        <Bar dataKey="transactions" name="Transactions" fill="#8B5CF6" radius={[0, 6, 6, 0]} barSize={14} />
      </BarChart>
    </ResponsiveContainer>
  );
}
