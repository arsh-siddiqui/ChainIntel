import { describe, expect, it } from "vitest";
import { caseSchema, investigateSchema, monitorSchema } from "@/lib/validators";

describe("investigateSchema", () => {
  it("accepts a Bitcoin address with auto detection", () => {
    const parsed = investigateSchema.safeParse({ address: "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", blockchain: "auto" });
    expect(parsed.success).toBe(true);
  });

  it("trims surrounding whitespace", () => {
    const parsed = investigateSchema.parse({ address: "  1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa  ", blockchain: "bitcoin" });
    expect(parsed.address).toBe("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa");
  });

  it("rejects short addresses", () => {
    expect(investigateSchema.safeParse({ address: "ab", blockchain: "auto" }).success).toBe(false);
  });

  it("rejects unknown chains (live-only: bitcoin, ethereum, bsc)", () => {
    expect(investigateSchema.safeParse({ address: "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", blockchain: "solana" }).success).toBe(false);
  });
});

describe("monitorSchema", () => {
  it("accepts a threshold rule", () => {
    const parsed = monitorSchema.safeParse({ wallet_address: "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", direction: "outgoing", amount_threshold: 1.0, on_threat_match: true, flagged_counterparty: false });
    expect(parsed.success).toBe(true);
  });

  it("rejects negative thresholds", () => {
    expect(monitorSchema.safeParse({ wallet_address: "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", amount_threshold: -1 }).success).toBe(false);
  });
});

describe("caseSchema", () => {
  it("requires a meaningful title", () => {
    expect(caseSchema.safeParse({ title: "ab" }).success).toBe(false);
    expect(caseSchema.safeParse({ title: "Ransomware trace" }).success).toBe(true);
  });
});
