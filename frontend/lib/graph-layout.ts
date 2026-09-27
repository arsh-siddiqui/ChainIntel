import type { GraphData, GraphEdge, GraphNode } from "@/types";

export interface GraphProcessOptions {
  clusterLeaves: boolean;
  minAmount: number;
  flaggedOnly: boolean;
  hiddenTypes?: Set<string>;
  searchQuery?: string;
  expandedClusters?: Set<string>;
}

export interface ProcessedGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  positions: Map<string, { x: number; y: number }>;
  clusteredCount: number;
  originalNodeCount: number;
}

/**
 * Filter and optionally cluster low-value leaf nodes to convert
 * overwhelming 100+ node visual webs into clean, legible forensic flows.
 */
export function processGraphData(
  graph: GraphData,
  options: GraphProcessOptions,
  layoutMode: "flow" | "radial" = "flow"
): ProcessedGraph {
  const focus = graph.focus_address || graph.nodes[0]?.id || "";
  const originalNodeCount = graph.nodes.length;

  if (!graph.nodes.length) {
    return {
      nodes: [],
      edges: [],
      positions: new Map(),
      clusteredCount: 0,
      originalNodeCount: 0,
    };
  }

  // 1. Filter out hidden types and minimum amount
  let filteredNodes = graph.nodes.filter((node) => {
    if (node.id === focus) return true;
    if (options.hiddenTypes?.has(node.type)) return false;
    if (options.flaggedOnly && node.risk === "clear" && (!node.categories || node.categories.length === 0)) {
      return false;
    }
    return true;
  });

  const validNodeIds = new Set(filteredNodes.map((n) => n.id));

  let filteredEdges = graph.edges.filter((edge) => {
    if (!validNodeIds.has(edge.source) || !validNodeIds.has(edge.target)) return false;
    if (options.minAmount > 0 && edge.amount < options.minAmount) {
      // Don't filter out edges directly connected to focus or flagged nodes
      const src = graph.nodes.find((n) => n.id === edge.source);
      const tgt = graph.nodes.find((n) => n.id === edge.target);
      const isImportant = src?.focus || tgt?.focus || src?.risk === "high" || tgt?.risk === "high";
      if (!isImportant) return false;
    }
    return true;
  });

  // Re-prune any orphaned non-focus nodes
  const connectedIds = new Set<string>();
  connectedIds.add(focus);
  for (const e of filteredEdges) {
    connectedIds.add(e.source);
    connectedIds.add(e.target);
  }
  filteredNodes = filteredNodes.filter((n) => connectedIds.has(n.id));

  let finalNodes = [...filteredNodes];
  let finalEdges = [...filteredEdges];
  let clusteredCount = 0;

  // 2. Smart Clustering of Leaf Wallets
  if (options.clusterLeaves) {
    // Degree map based on current filtered edges
    const degreeMap = new Map<string, number>();
    for (const e of finalEdges) {
      degreeMap.set(e.source, (degreeMap.get(e.source) ?? 0) + 1);
      degreeMap.set(e.target, (degreeMap.get(e.target) ?? 0) + 1);
    }

    // Leaf nodes eligible for clustering:
    // - Must have degree == 1
    // - Not the focus node
    // - Risk is "clear"
    // - Type is "wallet" or "unknown" (keep exchanges, mixers, ransomware, scams, victims visible!)
    const eligibleLeaves = new Set<string>();
    for (const node of finalNodes) {
      if (
        node.id !== focus &&
        (degreeMap.get(node.id) ?? 0) === 1 &&
        node.risk === "clear" &&
        (node.type === "wallet" || node.type === "unknown") &&
        (!node.categories || node.categories.length === 0)
      ) {
        eligibleLeaves.add(node.id);
      }
    }

    // Group eligible leaf nodes by their single parent and flow direction
    type LeafGroup = {
      parent: string;
      direction: "in" | "out";
      leaves: GraphNode[];
      edges: GraphEdge[];
    };

    const groupKeyMap = new Map<string, LeafGroup>();

    for (const edge of finalEdges) {
      if (eligibleLeaves.has(edge.source) && !eligibleLeaves.has(edge.target)) {
        // Leaf is sender -> flows into parent (target)
        const parent = edge.target;
        const key = `in:${parent}`;
        const existing = groupKeyMap.get(key) ?? {
          parent,
          direction: "in",
          leaves: [],
          edges: [],
        };
        const node = finalNodes.find((n) => n.id === edge.source);
        if (node) existing.leaves.push(node);
        existing.edges.push(edge);
        groupKeyMap.set(key, existing);
      } else if (eligibleLeaves.has(edge.target) && !eligibleLeaves.has(edge.source)) {
        // Leaf is recipient -> flows out from parent (source)
        const parent = edge.source;
        const key = `out:${parent}`;
        const existing = groupKeyMap.get(key) ?? {
          parent,
          direction: "out",
          leaves: [],
          edges: [],
        };
        const node = finalNodes.find((n) => n.id === edge.target);
        if (node) existing.leaves.push(node);
        existing.edges.push(edge);
        groupKeyMap.set(key, existing);
      }
    }

    const removedLeafIds = new Set<string>();
    const clusterNodesToAdd: GraphNode[] = [];
    const clusterEdgesToAdd: GraphEdge[] = [];

    for (const [key, group] of groupKeyMap.entries()) {
      // Cluster only if at least 3 leaves to avoid useless single/pair clusters
      const clusterId = `cluster_${key.replace(":", "_")}`;
      const isExpanded = options.expandedClusters?.has(clusterId);

      if (group.leaves.length >= 3 && !isExpanded) {
        const totalAmount = group.edges.reduce((sum, e) => sum + e.amount, 0);
        const totalCount = group.edges.reduce((sum, e) => sum + e.count, 0);
        const label =
          group.direction === "in"
            ? `${group.leaves.length} Deposit Senders`
            : `${group.leaves.length} Recipients`;

        clusterNodesToAdd.push({
          id: clusterId,
          label,
          type: "cluster",
          risk: "clear",
          focus: false,
          tx_count: totalCount,
          categories: ["Aggregated Cluster"],
          clusterCount: group.leaves.length,
          clusterAmount: Number(totalAmount.toFixed(8)),
          clusterMembers: group.leaves,
        });

        clusterEdgesToAdd.push({
          source: group.direction === "in" ? clusterId : group.parent,
          target: group.direction === "in" ? group.parent : clusterId,
          amount: Number(totalAmount.toFixed(8)),
          asset: group.edges[0]?.asset || "BTC",
          tx_hash: group.edges[0]?.tx_hash || "",
          tx_hashes: group.edges.flatMap((e) => e.tx_hashes).slice(0, 20),
          timestamp: group.edges[0]?.timestamp || null,
          count: totalCount,
        });

        for (const l of group.leaves) {
          removedLeafIds.add(l.id);
        }
        clusteredCount += group.leaves.length;
      }
    }

    // Filter out clustered leaf nodes and their individual edges
    finalNodes = finalNodes.filter((n) => !removedLeafIds.has(n.id)).concat(clusterNodesToAdd);
    finalEdges = finalEdges
      .filter((e) => !removedLeafIds.has(e.source) && !removedLeafIds.has(e.target))
      .concat(clusterEdgesToAdd);
  }

  // 3. Compute deterministic layout positions
  const positions =
    layoutMode === "radial"
      ? computeRadialLayout(finalNodes, finalEdges, focus)
      : computeFlowLayout(finalNodes, finalEdges, focus);

  return {
    nodes: finalNodes,
    edges: finalEdges,
    positions,
    clusteredCount,
    originalNodeCount,
  };
}

/**
 * Clean Hierarchical Directed DAG layout:
 * - Upstream senders flow from the LEFT into the focus node.
 * - Downstream recipients flow from the focus node to the RIGHT.
 * - Each hop level occupies a clear rank column.
 * - Nodes within a rank are vertically centered with generous spacing and double-lane staggering if dense.
 */
function computeFlowLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focus: string
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  if (!nodes.length) return positions;

  positions.set(focus, { x: 0, y: 0 });

  // Directed adjacency
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const e of edges) {
    outgoing.set(e.source, [...(outgoing.get(e.source) ?? []), e.target]);
    incoming.set(e.target, [...(incoming.get(e.target) ?? []), e.source]);
  }

  // Rank map: 0 for focus, negative for upstream (-1, -2...), positive for downstream (+1, +2...)
  const rankMap = new Map<string, number>();
  rankMap.set(focus, 0);

  // Upstream BFS (traverse incoming backwards)
  const upQueue: string[] = [focus];
  while (upQueue.length > 0) {
    const cur = upQueue.shift()!;
    const curRank = rankMap.get(cur) ?? 0;
    for (const sender of incoming.get(cur) ?? []) {
      if (!rankMap.has(sender)) {
        rankMap.set(sender, curRank - 1);
        upQueue.push(sender);
      }
    }
  }

  // Downstream BFS (traverse outgoing forwards)
  const downQueue: string[] = [focus];
  while (downQueue.length > 0) {
    const cur = downQueue.shift()!;
    const curRank = rankMap.get(cur) ?? 0;
    for (const recipient of outgoing.get(cur) ?? []) {
      if (!rankMap.has(recipient)) {
        rankMap.set(recipient, curRank + 1);
        downQueue.push(recipient);
      }
    }
  }

  // Assign any remaining disconnected nodes to rank +1
  for (const n of nodes) {
    if (!rankMap.has(n.id)) {
      rankMap.set(n.id, 1);
    }
  }

  // Group nodes by rank
  const rankGroups = new Map<number, GraphNode[]>();
  for (const node of nodes) {
    if (node.id === focus) continue;
    const rank = rankMap.get(node.id) ?? 1;
    rankGroups.set(rank, [...(rankGroups.get(rank) ?? []), node]);
  }

  const RANK_X_STEP = 360;
  const ROW_HEIGHT = 90;

  for (const [rank, groupNodes] of rankGroups.entries()) {
    // Sort group nodes: high-risk entities first, then clusters, then standard wallets
    groupNodes.sort((a, b) => {
      const aWeight = a.risk === "high" ? 3 : a.type === "cluster" ? 2 : a.type !== "wallet" ? 1 : 0;
      const bWeight = b.risk === "high" ? 3 : b.type === "cluster" ? 2 : b.type !== "wallet" ? 1 : 0;
      return bWeight - aWeight;
    });

    const count = groupNodes.length;
    const baseX = rank * RANK_X_STEP;

    if (count <= 10) {
      // Single vertical centered column
      groupNodes.forEach((node, index) => {
        const y = (index - (count - 1) / 2) * ROW_HEIGHT;
        positions.set(node.id, { x: baseX, y });
      });
    } else {
      // Staggered double-lane layout to prevent excessively tall or dense columns
      const lanes = 2;
      const laneWidth = 140;
      groupNodes.forEach((node, index) => {
        const lane = index % lanes;
        const laneIndex = Math.floor(index / lanes);
        const laneCount = Math.ceil(count / lanes);

        const xOffset = (lane - (lanes - 1) / 2) * laneWidth;
        const x = baseX + (rank < 0 ? -xOffset : xOffset);
        const y = (laneIndex - (laneCount - 1) / 2) * ROW_HEIGHT;

        positions.set(node.id, { x, y });
      });
    }
  }

  return positions;
}

/**
 * Concentric Radial Orbit layout:
 * - Focus node at center (0, 0)
 * - Hop 1 at radius 340px, Hop 2 at radius 600px
 * - Upstream nodes placed on left arc (110° to 250°)
 * - Downstream nodes placed on right arc (-70° to 70°)
 */
function computeRadialLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focus: string
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  if (!nodes.length) return positions;

  positions.set(focus, { x: 0, y: 0 });

  const incoming = new Set<string>();
  const outgoing = new Set<string>();
  for (const e of edges) {
    if (e.target === focus) incoming.add(e.source);
    if (e.source === focus) outgoing.add(e.target);
  }

  const upstreamNodes = nodes.filter((n) => n.id !== focus && incoming.has(n.id));
  const downstreamNodes = nodes.filter((n) => n.id !== focus && outgoing.has(n.id));
  const otherNodes = nodes.filter(
    (n) => n.id !== focus && !incoming.has(n.id) && !outgoing.has(n.id)
  );

  const RADIUS_1 = 340;
  const RADIUS_2 = 600;

  // Upstream on the left semicircle: 110 deg to 250 deg (in radians)
  const upStart = (110 * Math.PI) / 180;
  const upEnd = (250 * Math.PI) / 180;
  const upCount = upstreamNodes.length;

  upstreamNodes.forEach((node, idx) => {
    const angle = upCount === 1 ? (upStart + upEnd) / 2 : upStart + (idx / (upCount - 1)) * (upEnd - upStart);
    const x = Math.cos(angle) * RADIUS_1;
    const y = Math.sin(angle) * RADIUS_1;
    positions.set(node.id, { x, y });
  });

  // Downstream on the right semicircle: -70 deg to 70 deg (in radians)
  const downStart = (-70 * Math.PI) / 180;
  const downEnd = (70 * Math.PI) / 180;
  const downCount = downstreamNodes.length;

  downNodesLayout(downstreamNodes, downStart, downEnd, RADIUS_1, positions);

  // Outer ring for secondary/other nodes
  if (otherNodes.length > 0) {
    downNodesLayout(otherNodes, -Math.PI, Math.PI, RADIUS_2, positions);
  }

  return positions;
}

function downNodesLayout(
  nodes: GraphNode[],
  startAngle: number,
  endAngle: number,
  radius: number,
  positions: Map<string, { x: number; y: number }>
) {
  const count = nodes.length;
  nodes.forEach((node, idx) => {
    const angle = count === 1 ? (startAngle + endAngle) / 2 : startAngle + (idx / (count - 1)) * (endAngle - startAngle);
    const x = Math.cos(angle) * radius;
    const y = Math.sin(angle) * radius;
    positions.set(node.id, { x, y });
  });
}
