export const INVESTIGATOR = "Investigator";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/wallet", label: "Investigate Wallet" },
  { href: "/transactions", label: "Transaction Explorer" },
  { href: "/graph", label: "Graph Analysis" },
  { href: "/threat-intelligence", label: "Threat Intelligence" },
  { href: "/osint", label: "OSINT Correlation" },
  { href: "/alerts", label: "Alerts & Monitoring" },
  { href: "/investigations", label: "Investigation Cases" },
  { href: "/evidence", label: "Evidence" },
  { href: "/reports", label: "Reports" },
  // { href: "/settings", label: "Settings" },
] as const;

export const CHAIN_OPTIONS = [
  { value: "auto", label: "AUTO (detect)" },
  { value: "bitcoin", label: "Bitcoin (BTC)" },
  { value: "ethereum", label: "Ethereum (ETH)" },
  { value: "bsc", label: "BNB Smart Chain (BNB)" },
  { value: "polygon", label: "Polygon (MATIC)" },
  { value: "solana", label: "Solana (SOL)" },
] as const;

export const THREAT_CATEGORIES = [
  "Ransomware",
  "Scam",
  "Phishing",
  "Blacklist",
  "Fraud",
  "Exploit",
  "Suspicious Service",
  "Unknown",
] as const;

export const EVIDENCE_TYPES = [
  "Screenshot",
  "Transaction Hash",
  "Wallet Address",
  "API Response",
  "OSINT Result",
  "Document",
  "Analyst Note",
  "Graph Snapshot",
] as const;

export const ALERT_STATUSES = ["NEW", "ACKNOWLEDGED", "INVESTIGATING", "RESOLVED"] as const;
export const CASE_STATUSES = ["OPEN", "UNDER_INVESTIGATION", "ON_HOLD", "RESOLVED", "CLOSED"] as const;
export const CASE_PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

export const RISK_BAND_STYLES: Record<string, string> = {
  CLEAR: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30",
  LOW: "bg-teal-50 text-teal-800 border-teal-300 dark:bg-teal-500/15 dark:text-teal-300 dark:border-teal-500/30",
  MODERATE: "bg-amber-50 text-amber-900 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30",
  ELEVATED: "bg-orange-50 text-orange-900 border-orange-300 dark:bg-orange-500/15 dark:text-orange-300 dark:border-orange-500/30",
  HIGH: "bg-rose-50 text-rose-900 border-rose-300 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30",
};

export const SEVERITY_STYLES: Record<string, string> = {
  INFO: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  LOW: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30",
  MEDIUM: "bg-amber-50 text-amber-900 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30",
  HIGH: "bg-orange-50 text-orange-900 border-orange-300 dark:bg-orange-500/15 dark:text-orange-300 dark:border-orange-500/30",
  CRITICAL: "bg-rose-50 text-rose-900 border-rose-300 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30",
};

export const ALERT_STATUS_STYLES: Record<string, string> = {
  NEW: "bg-sky-50 text-sky-800 border-sky-300 dark:bg-sky-500/15 dark:text-sky-300 dark:border-sky-500/30",
  ACKNOWLEDGED: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  INVESTIGATING: "bg-purple-50 text-purple-800 border-purple-300 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30",
  RESOLVED: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30",
};

export const CASE_STATUS_STYLES: Record<string, string> = {
  OPEN: "bg-sky-50 text-sky-800 border-sky-300 dark:bg-sky-500/15 dark:text-sky-300 dark:border-sky-500/30",
  UNDER_INVESTIGATION: "bg-purple-50 text-purple-800 border-purple-300 dark:bg-purple-500/15 dark:text-purple-300 dark:border-purple-500/30",
  ON_HOLD: "bg-amber-50 text-amber-900 border-amber-300 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30",
  RESOLVED: "bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30",
  CLOSED: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
};

export const PRIORITY_STYLES: Record<string, string> = {
  LOW: "bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
  MEDIUM: "bg-sky-50 text-sky-800 border-sky-300 dark:bg-sky-500/15 dark:text-sky-300 dark:border-sky-500/30",
  HIGH: "bg-orange-50 text-orange-900 border-orange-300 dark:bg-orange-500/15 dark:text-orange-300 dark:border-orange-500/30",
  CRITICAL: "bg-rose-50 text-rose-900 border-rose-300 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30",
};

/** Node type → color for the transaction graph (light-theme palette). */
export const GRAPH_NODE_COLORS: Record<string, { bg: string; border: string; text: string; label: string }> = {
  victim: { bg: "#EFF6FF", border: "#2563EB", text: "#1D4ED8", label: "Victim" },
  wallet: { bg: "#FFFFFF", border: "#94A3B8", text: "#334155", label: "Wallet" },
  ransomware: { bg: "#FEF2F2", border: "#DC2626", text: "#B91C1C", label: "Ransomware" },
  scam: { bg: "#FEF2F2", border: "#EF4444", text: "#B91C1C", label: "Scam" },
  exchange: { bg: "#F0FDFA", border: "#14B8A6", text: "#0F766E", label: "Exchange" },
  mixer: { bg: "#FDF4FF", border: "#A855F7", text: "#7E22CE", label: "Mixer/Service" },
  intermediate: { bg: "#FFFBEB", border: "#F59E0B", text: "#B45309", label: "Intermediate" },
  aggregator: { bg: "#FFF7ED", border: "#F97316", text: "#C2410C", label: "Aggregator" },
  contract: { bg: "#F5F3FF", border: "#8B5CF6", text: "#6D28D9", label: "Contract" },
  cluster: { bg: "#EEF2FF", border: "#6366F1", text: "#4338CA", label: "Cluster" },
  unknown: { bg: "#F8FAFC", border: "#CBD5E1", text: "#475569", label: "Unknown" },
};

export const OSINT_STATUS_STYLES: Record<string, string> = {
  FOUND: "bg-purple-50 text-purple-700 border-purple-200",
  NOT_FOUND: "bg-slate-100 text-slate-600 border-slate-200",
  UNAVAILABLE: "bg-amber-50 text-amber-700 border-amber-200",
  ERROR: "bg-red-50 text-red-700 border-red-200",
  REQUIRES_CONFIGURATION: "bg-amber-50 text-amber-700 border-amber-200",
};
