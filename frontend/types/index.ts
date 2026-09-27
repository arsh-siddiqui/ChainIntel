export interface Envelope<T> {
  success: boolean;
  data: T;
  meta: Record<string, unknown>;
  error: { code: string; message: string } | null;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ValidationResult {
  valid: boolean;
  blockchain: string | null;
  possible_chains: string[];
  reason: string;
}

export interface WalletSummary {
  address: string;
  blockchain: string;
  label: string | null;
  balance: number;
  pending_balance?: number | null;
  asset: string;
  transaction_count: number;
  first_activity: string | null;
  last_activity: string | null;
  incoming_volume: number;
  outgoing_volume: number;
  unique_counterparties: number;
  explorer_url: string | null;
  provider?: string | null;
  is_demo: boolean;
}

export interface NormalizedTx {
  tx_hash: string;
  blockchain: string;
  from_address: string | null;
  to_address: string | null;
  amount: number;
  asset: string;
  timestamp: string | null;
  block_number: number | null;
  confirmations: number;
  status: string;
  fee: number | null;
  direction?: "incoming" | "outgoing" | null;
  is_demo: boolean;
}

export interface ThreatFinding {
  id?: number;
  wallet_address: string;
  blockchain: string;
  category: string;
  label: string;
  source: string;
  reference_url: string | null;
  confidence: number;
  first_seen: string | null;
  last_seen: string | null;
  notes: string | null;
  status?: string;
  is_demo: boolean;
}

export interface OSINTResult {
  source_name: string;
  source_category: string;
  query: string;
  status: "FOUND" | "NOT_FOUND" | "UNAVAILABLE" | "ERROR" | "REQUIRES_CONFIGURATION";
  finding: string | null;
  confidence: number;
  reference_url: string | null;
  external_search_url: string | null;
  notes: string | null;
  is_demo: boolean;
  record_type?: string | null;
}

export interface OSINTCorrelation {
  query: string;
  results: OSINTResult[];
  found_count: number;
  provider_count: number;
  simulated: boolean;
  note: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  risk: "clear" | "elevated" | "high";
  focus: boolean;
  tx_count: number;
  categories?: string[];
  clusterCount?: number;
  clusterAmount?: number;
  clusterMembers?: GraphNode[];
}

export interface GraphEdge {
  source: string;
  target: string;
  amount: number;
  asset: string;
  tx_hash: string;
  tx_hashes: string[];
  timestamp: string | null;
  count: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: { node_count: number; edge_count: number; unique_wallets: number; total_amount: number; truncated: boolean; hops: number };
  focus_address: string;
}

export interface TracePathEdge {
  source: string;
  target: string;
  amount: number;
  asset: string;
  tx_hash: string | null;
  timestamp: string | null;
}

export interface TraceResult {
  source: string;
  direction: "outgoing" | "incoming";
  max_hops: number;
  nodes_explored: number;
  disclaimer: string;
  suspicious_nodes: { address: string; label: string; categories: string[]; sources: string[]; confidence: number }[];
  found?: boolean;
  path?: string[];
  path_edges?: TracePathEdge[];
  hops?: number;
  total_amount?: number;
  paths?: { path: string[]; hops: number; amount: number }[];
  destination_label?: string;
  note?: string;
  levels?: { hop: number; addresses: { address: string; label: string; suspicious: boolean }[] }[];
}

export interface RiskIndicator {
  name: string;
  description: string;
  weight: number;
  source: string;
  status: "TRIGGERED" | "NOT_TRIGGERED" | "UNAVAILABLE";
  evidence: string;
}

export interface RiskAssessment {
  score: number;
  max_score: number;
  band: "LOW" | "MODERATE" | "ELEVATED" | "HIGH";
  indicators: RiskIndicator[];
  disclaimer: string;
}

export interface InvestigationBundle {
  investigation_id: number | null;
  generated_at: string;
  mode: "DEMO" | "LIVE";
  address: string;
  blockchain: string;
  provider: { name: string; status: string; is_demo: boolean };
  wallet: WalletSummary;
  transactions: NormalizedTx[];
  threats: ThreatFinding[];
  counterparty_threats: ThreatFinding[];
  osint: OSINTCorrelation;
  graph: GraphData;
  fund_flow: TraceResult;
  risk: RiskAssessment;
}

export interface InvestigationSummary {
  id: number;
  case_id: number | null;
  title: string;
  wallet_address: string;
  blockchain: string;
  status: string;
  risk_level: string | null;
  risk_score: number | null;
  investigator: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: number;
  wallet_address: string;
  rule: Record<string, unknown> | null;
  transaction_hash: string | null;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "NEW" | "ACKNOWLEDGED" | "INVESTIGATING" | "RESOLVED";
  title: string;
  message: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface Monitor {
  id: number;
  wallet_address: string;
  blockchain: string;
  label: string | null;
  rules: { direction?: string; amount_threshold?: number | null; on_threat_match?: boolean; flagged_counterparty?: boolean };
  status: "ACTIVE" | "PAUSED";
  last_checked: string | null;
  last_tx_hash: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface CaseRecord {
  id: number;
  case_number: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  investigator: string;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseRecord {
  investigations: InvestigationSummary[];
  evidence: EvidenceRecord[];
  reports: ReportSummary[];
  timeline: CaseEvent[];
}

export interface CaseEvent {
  id: number;
  case_id: number;
  event_type: string;
  description: string;
  created_at: string;
}

export interface EvidenceRecord {
  id: number;
  case_id: number | null;
  type: string;
  title: string;
  description: string | null;
  source: string | null;
  file_name: string | null;
  sha256: string | null;
  size_bytes: number;
  has_file: boolean;
  created_at: string;
  integrity_verified?: boolean;
}

export interface ReportSummary {
  id: string;
  case_id: number | null;
  wallet_address: string;
  blockchain: string;
  title: string;
  mode: string;
  created_at: string;
  payload?: ReportPayload;
}

export interface ReportPayload {
  report_id: string;
  generated_at: string;
  mode: string;
  app_version: string;
  case: { id: number; case_number: string; title: string; status: string; priority: string } | null;
  wallet: string;
  blockchain: string;
  wallet_summary: Partial<WalletSummary>;
  transactions: NormalizedTx[];
  threat_findings: ThreatFinding[];
  osint_findings: OSINTResult[];
  risk_indicators: RiskIndicator[];
  risk: RiskAssessment;
  fund_flow: Partial<TraceResult>;
  evidence: EvidenceRecord[];
  timeline: CaseEvent[];
  investigation: InvestigationSummary | null;
  status: string;
  analyst_notes: string | null;
  disclaimers: string[];
}

export interface DashboardSummary {
  kpis: {
    total_investigations: number;
    suspicious_wallets: number;
    transactions_analyzed: number;
    active_alerts: number;
    threat_matches: number;
    wallets_monitored: number;
    open_cases: number;
    reports_generated: number;
  };
  activity: { date: string; incoming: number; outgoing: number; count: number }[];
  threat_distribution: { category: string; count: number }[];
  risk_distribution: { risk_level: string; count: number }[];
  investigation_status: { status: string; count: number }[];
  top_counterparties: { address: string; transactions: number; volume: number }[];
  recent_investigations: InvestigationSummary[];
  recent_alerts: Alert[];
}

export interface HealthData {
  status: string;
  mode: "DEMO" | "LIVE";
  version: string;
  database: string;
}

export interface ProviderStatus {
  name: string;
  blockchain: string;
  status: "CONFIGURED" | "NOT_CONFIGURED";
  key_configured: boolean | null;
  is_demo: boolean;
}

export interface OSINTSourceStatus {
  name: string;
  source_category: string;
  automated: boolean;
  is_demo: boolean;
  status: "DEMO" | "LINK_ONLY";
}

export interface ImportStats {
  received: number;
  valid: number;
  invalid: number;
  duplicates: number;
  inserted: number;
  updated: number;
  errors: string[];
}
