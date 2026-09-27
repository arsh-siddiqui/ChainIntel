import { describe, expect, it } from "vitest";
import { confidencePercent, formatCrypto, formatDateTime, titleCase, truncateMiddle } from "@/lib/formatters";

describe("formatCrypto", () => {
  it("formats whole amounts with 2 decimals maximum", () => {
    expect(formatCrypto(1500.5, "BTC")).toContain("1,500.5");
    expect(formatCrypto(1500.5, "BTC")).toContain("BTC");
  });

  it("formats dust amounts with enough precision", () => {
    expect(formatCrypto(0.00012345, "BTC")).toContain("0.000123");
  });

  it("renders an em dash for missing values", () => {
    expect(formatCrypto(null, "BTC")).toContain("—");
  });
});

describe("truncateMiddle", () => {
  it("keeps short strings intact", () => {
    expect(truncateMiddle("DEMO-TX-1", 10, 6)).toBe("DEMO-TX-1");
  });

  it("truncates long identifiers with a middle ellipsis", () => {
    const result = truncateMiddle("DEMO-RANSOM-0001", 6, 5);
    expect(result).toContain("…");
    expect(result.startsWith("DEMO-R")).toBe(true);
    expect(result.endsWith("-0001")).toBe(true);
  });
});

describe("formatDateTime", () => {
  it("formats ISO timestamps", () => {
    expect(formatDateTime("2026-03-01T09:30:00Z")).toMatch(/^2026-03-01 \d{2}:\d{2}$/);
  });

  it("returns a dash for null", () => {
    expect(formatDateTime(null)).toBe("—");
  });
});

describe("confidencePercent", () => {
  it("converts 0-1 confidence to percent", () => {
    expect(confidencePercent(0.92)).toBe("92%");
  });
});

describe("titleCase", () => {
  it("humanizes snake_case statuses", () => {
    expect(titleCase("UNDER_INVESTIGATION")).toBe("Under Investigation");
  });
});
