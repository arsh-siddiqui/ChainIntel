import { z } from "zod";

export const investigateSchema = z.object({
  address: z.string().trim().min(4, "Enter a wallet address").max(255),
  blockchain: z.enum(["auto", "bitcoin", "ethereum", "bsc"]),
});
export type InvestigateForm = z.infer<typeof investigateSchema>;

export const monitorSchema = z.object({
  wallet_address: z.string().trim().min(4, "Wallet address is required").max(255),
  label: z.string().trim().max(255).optional().or(z.literal("")),
  direction: z.enum(["any", "incoming", "outgoing"]),
  amount_threshold: z
    .union([z.coerce.number().positive("Threshold must be positive"), z.literal("").transform(() => null), z.undefined()])
    .optional(),
  on_threat_match: z.boolean(),
  flagged_counterparty: z.boolean(),
});
export type MonitorForm = z.infer<typeof monitorSchema>;

export const caseSchema = z.object({
  title: z.string().trim().min(3, "Title must be at least 3 characters").max(255),
  description: z.string().trim().max(8000).optional().or(z.literal("")),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]).default("MEDIUM"),
});
export type CaseForm = z.infer<typeof caseSchema>;

export const evidenceNoteSchema = z.object({
  title: z.string().trim().min(2, "Title is required").max(255),
  evidence_type: z.string().min(1),
  description: z.string().trim().max(2000).optional().or(z.literal("")),
  content_text: z.string().trim().min(1, "Note content is required").max(8000),
});
export type EvidenceNoteForm = z.infer<typeof evidenceNoteSchema>;

export const restrictedSourceSchema = z.object({
  wallet_address: z.string().trim().min(4, "Wallet address is required").max(255),
  source: z.string().trim().min(1, "Source is required").max(255),
  record_type: z.enum(["VERIFIED_SOURCE", "IMPORTED_INTELLIGENCE", "ANALYST_NOTE", "UNAVAILABLE"]),
  finding: z.string().trim().min(1, "Finding is required").max(4000),
  reference_url: z
    .string()
    .trim()
    .max(512)
    .refine((v) => v === "" || /^https?:\/\//.test(v), "URL must start with http:// or https://")
    .optional()
    .or(z.literal("")),
  confidence: z.coerce.number().min(0).max(1),
});
export type RestrictedSourceForm = z.infer<typeof restrictedSourceSchema>;

export const traceSchema = z.object({
  wallet_address: z.string().trim().min(4, "Source wallet is required").max(255),
  target_address: z.string().trim().max(255).optional().or(z.literal("")),
  direction: z.enum(["outgoing", "incoming"]),
  max_hops: z.coerce.number().int().min(1).max(7),
});
export type TraceForm = z.infer<typeof traceSchema>;
