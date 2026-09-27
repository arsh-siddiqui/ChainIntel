import { describe, expect, it } from "vitest";
import { processGraphData } from "./graph-layout";
import type { GraphData } from "@/types";

describe("processGraphData", () => {
  const sampleGraph: GraphData = {
    focus_address: "target_wallet",
    nodes: [
      { id: "target_wallet", label: "Target", type: "wallet", risk: "clear", focus: true, tx_count: 10 },
      // 5 trivial leaf senders
      { id: "sender_1", label: "Sender 1", type: "wallet", risk: "clear", focus: false, tx_count: 1 },
      { id: "sender_2", label: "Sender 2", type: "wallet", risk: "clear", focus: false, tx_count: 1 },
      { id: "sender_3", label: "Sender 3", type: "wallet", risk: "clear", focus: false, tx_count: 1 },
      { id: "sender_4", label: "Sender 4", type: "wallet", risk: "clear", focus: false, tx_count: 1 },
      { id: "sender_5", label: "Sender 5", type: "wallet", risk: "clear", focus: false, tx_count: 1 },
      // 1 high risk sender that should NOT be clustered
      { id: "ransomware_1", label: "LockBit", type: "ransomware", risk: "high", focus: false, tx_count: 2 },
    ],
    edges: [
      { source: "sender_1", target: "target_wallet", amount: 0.0001, asset: "BTC", count: 1, tx_hash: "h1", tx_hashes: ["h1"], timestamp: null },
      { source: "sender_2", target: "target_wallet", amount: 0.0002, asset: "BTC", count: 1, tx_hash: "h2", tx_hashes: ["h2"], timestamp: null },
      { source: "sender_3", target: "target_wallet", amount: 0.0003, asset: "BTC", count: 1, tx_hash: "h3", tx_hashes: ["h3"], timestamp: null },
      { source: "sender_4", target: "target_wallet", amount: 0.0004, asset: "BTC", count: 1, tx_hash: "h4", tx_hashes: ["h4"], timestamp: null },
      { source: "sender_5", target: "target_wallet", amount: 0.0005, asset: "BTC", count: 1, tx_hash: "h5", tx_hashes: ["h5"], timestamp: null },
      { source: "ransomware_1", target: "target_wallet", amount: 1.5, asset: "BTC", count: 1, tx_hash: "h6", tx_hashes: ["h6"], timestamp: null },
    ],
    stats: {
      node_count: 7,
      edge_count: 6,
      unique_wallets: 7,
      total_amount: 1.5015,
      truncated: false,
      hops: 1,
    },
  };

  it("clusters trivial leaf senders while keeping high-risk entities unclustered", () => {
    const result = processGraphData(
      sampleGraph,
      {
        clusterLeaves: true,
        minAmount: 0,
        flaggedOnly: false,
      },
      "flow"
    );

    // Should have: Target (1), High-Risk Ransomware (1), and 1 Cluster Node for the 5 senders!
    expect(result.nodes.length).toBe(3);
    expect(result.clusteredCount).toBe(5);

    const clusterNode = result.nodes.find((n) => n.type === "cluster");
    expect(clusterNode).toBeDefined();
    expect(clusterNode?.clusterCount).toBe(5);
    expect(clusterNode?.clusterAmount).toBeCloseTo(0.0015, 4);

    const ransomwareNode = result.nodes.find((n) => n.id === "ransomware_1");
    expect(ransomwareNode).toBeDefined();
    expect(ransomwareNode?.risk).toBe("high");
  });

  it("unclusters when clusterLeaves is disabled", () => {
    const result = processGraphData(
      sampleGraph,
      {
        clusterLeaves: false,
        minAmount: 0,
        flaggedOnly: false,
      },
      "flow"
    );

    expect(result.nodes.length).toBe(7);
    expect(result.clusteredCount).toBe(0);
  });

  it("filters low amount transactions when minAmount is specified", () => {
    const result = processGraphData(
      sampleGraph,
      {
        clusterLeaves: false,
        minAmount: 0.01,
        flaggedOnly: false,
      },
      "flow"
    );

    // Target and ransomware_1 should remain; low amount senders (< 0.01) filtered out
    const nodeIds = result.nodes.map((n) => n.id);
    expect(nodeIds).toContain("target_wallet");
    expect(nodeIds).toContain("ransomware_1");
  });

  it("computes radial orbit positions without errors", () => {
    const result = processGraphData(
      sampleGraph,
      {
        clusterLeaves: true,
        minAmount: 0,
        flaggedOnly: false,
      },
      "radial"
    );

    expect(result.positions.get("target_wallet")).toEqual({ x: 0, y: 0 });
    expect(result.positions.size).toBe(result.nodes.length);
  });
});
