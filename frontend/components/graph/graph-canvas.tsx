"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toPng } from "html-to-image";
import {
  Download,
  Filter,
  Layers,
  Maximize2,
  Minimize2,
  Orbit,
  RotateCcw,
  Search,
  Share2,
  ShieldAlert,
  Sparkles,
  Workflow,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { GRAPH_NODE_COLORS } from "@/lib/constants";
import { formatCrypto, truncateMiddle } from "@/lib/formatters";
import { processGraphData } from "@/lib/graph-layout";
import type { GraphData, GraphNode, TraceResult } from "@/types";
import { Button } from "@/components/common/ui";
import { ClusterNode, CustomNodeData, EntityNode, FocusNode } from "./custom-nodes";
import { EntityInspector } from "./entity-inspector";

const nodeTypes = {
  focus: FocusNode,
  entity: EntityNode,
  cluster: ClusterNode,
};

interface GraphCanvasProps {
  graph: GraphData;
  trace?: TraceResult | null;
  showAmounts: boolean;
  showLabels: boolean;
  hiddenTypes?: Set<string>;
  minHeight?: number;
  onSetFocus?: (address: string) => void;
  onTraceFromHere?: (address: string) => void;
}

function GraphCanvasInner({
  graph,
  trace,
  showAmounts,
  showLabels,
  hiddenTypes,
  minHeight = 620,
  onSetFocus,
  onTraceFromHere,
}: GraphCanvasProps) {
  const { theme } = useTheme();
  const reactFlowInstance = useReactFlow();
  const [container, setContainer] = useState<HTMLDivElement | null>(null);

  // Layout & Filter States
  const [layoutMode, setLayoutMode] = useState<"flow" | "radial">("flow");
  const [clusterLeaves, setClusterLeaves] = useState<boolean>(true);
  const [minAmount, setMinAmount] = useState<number>(0);
  const [flaggedOnly, setFlaggedOnly] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Highlighted paths
  const pathAddresses = useMemo(() => new Set(trace?.path ?? []), [trace]);
  const pathEdgeKeys = useMemo(() => {
    const set = new Set<string>();
    for (const edge of trace?.path_edges ?? []) {
      set.add(`${edge.source}->${edge.target}`);
    }
    return set;
  }, [trace]);

  // Expand a specific cluster
  const handleExpandCluster = useCallback((clusterId: string) => {
    setExpandedClusters((prev) => {
      const next = new Set(prev);
      next.add(clusterId);
      return next;
    });
  }, []);

  // Compute processed graph and layout
  const processed = useMemo(() => {
    return processGraphData(
      graph,
      {
        clusterLeaves,
        minAmount,
        flaggedOnly,
        hiddenTypes,
        expandedClusters,
      },
      layoutMode
    );
  }, [graph, clusterLeaves, minAmount, flaggedOnly, hiddenTypes, expandedClusters, layoutMode]);

  // Construct ReactFlow nodes and edges
  useEffect(() => {
    const isDark = theme === "dark";

    const flowNodes: Node[] = processed.nodes.map((node) => {
      const isSelected = selectedNode?.id === node.id;
      const nodeType = node.focus ? "focus" : node.type === "cluster" ? "cluster" : "entity";

      return {
        id: node.id,
        type: nodeType,
        position: processed.positions.get(node.id) ?? { x: 0, y: 0 },
        data: {
          ...node,
          label: showLabels ? node.label : truncateMiddle(node.id, 8, 4),
          isSelected,
          onSelectNode: (n: GraphNode) => setSelectedNode(n),
          onExpandCluster: handleExpandCluster,
        } as CustomNodeData,
      };
    });

    const flowEdges: Edge[] = processed.edges.map((edge) => {
      const isPathEdge =
        pathEdgeKeys.has(`${edge.source}->${edge.target}`) ||
        pathEdgeKeys.has(`${edge.target}->${edge.source}`);
      const inPath = pathAddresses.has(edge.source) && pathAddresses.has(edge.target);
      const highlighted = isPathEdge || (pathAddresses.size > 0 && inPath);

      // Connected to selected node
      const isConnectedToSelected =
        selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);

      // Edge stroke width based on relative amount
      const baseWidth = Math.min(4.5, Math.max(1.5, Math.log10(edge.amount * 1000 + 1) * 1.2));
      const strokeWidth = highlighted ? 3.5 : isConnectedToSelected ? 2.8 : baseWidth;

      const strokeColor = highlighted
        ? isDark
          ? "#38BDF8"
          : "#2563EB"
        : isConnectedToSelected
        ? isDark
          ? "#818CF8"
          : "#4F46E5"
        : isDark
        ? "#334155"
        : "#CBD5E1";

      const arrowColor = highlighted
        ? isDark
          ? "#38BDF8"
          : "#2563EB"
        : isConnectedToSelected
        ? isDark
          ? "#818CF8"
          : "#4F46E5"
        : isDark
        ? "#475569"
        : "#94A3B8";

      return {
        id: `${edge.source}->${edge.target}`,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        label: showAmounts
          ? `${formatCrypto(edge.amount, edge.asset)}${edge.count > 1 ? ` (${edge.count})` : ""}`
          : undefined,
        labelStyle: {
          fontSize: 10,
          fontWeight: 600,
          fill: isDark ? "#E2E8F0" : "#334155",
        },
        labelBgStyle: {
          fill: isDark ? "#0F172A" : "#FFFFFF",
          fillOpacity: 0.92,
          rx: 4,
          ry: 4,
        },
        animated: highlighted,
        style: {
          stroke: strokeColor,
          strokeWidth,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: arrowColor,
          width: 14,
          height: 14,
        },
      };
    });

    setNodes(flowNodes);
    setEdges(flowEdges);

    // Auto-fit view after layout compute
    const timeout = setTimeout(() => {
      reactFlowInstance.fitView({ padding: 0.25, duration: 400 });
    }, 50);

    return () => clearTimeout(timeout);
  }, [
    processed,
    theme,
    selectedNode,
    showAmounts,
    showLabels,
    pathAddresses,
    pathEdgeKeys,
    handleExpandCluster,
    setNodes,
    setEdges,
    reactFlowInstance,
  ]);

  // Search node within graph
  const handleSearchNode = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const match = processed.nodes.find(
      (n) =>
        n.id.toLowerCase().includes(searchQuery.toLowerCase().trim()) ||
        n.label.toLowerCase().includes(searchQuery.toLowerCase().trim())
    );
    if (match) {
      setSelectedNode(match);
      const pos = processed.positions.get(match.id);
      if (pos) {
        reactFlowInstance.setCenter(pos.x, pos.y, { zoom: 1.2, duration: 600 });
      }
    }
  };

  const exportPng = useCallback(async () => {
    if (!container) return;
    const isDark = theme === "dark";
    const dataUrl = await toPng(container, {
      backgroundColor: isDark ? "#0B1120" : "#F8FAFC",
      pixelRatio: 2,
    });
    const link = document.createElement("a");
    link.download = `chainintel-graph-${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  }, [container, theme]);

  const exportJson = useCallback(() => {
    const blob = new Blob([JSON.stringify(graph, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.download = `chainintel-graph-${Date.now()}.json`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  }, [graph]);

  const isDark = theme === "dark";

  return (
    <div className="relative flex flex-col gap-2">
      {/* Smart Forensic Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white/90 p-2.5 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex flex-wrap items-center gap-1.5">
          {/* Smart Clustering Toggle */}
          <button
            type="button"
            onClick={() => setClusterLeaves(!clusterLeaves)}
            className={`flex items-center gap-1.5 rounded-xl border px-2.5 py-1 text-xs font-semibold transition-all ${
              clusterLeaves
                ? "border-indigo-400 bg-indigo-50/80 text-indigo-700 shadow-sm dark:border-indigo-500 dark:bg-indigo-950/40 dark:text-indigo-300"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            }`}
            title="Cluster minor leaf wallets to simplify the flow graph"
          >
            <Sparkles size={13} className={clusterLeaves ? "text-indigo-600 dark:text-indigo-400 animate-spin-slow" : "text-slate-400"} />
            <span>Smart Cluster</span>
            {processed.clusteredCount > 0 && clusterLeaves && (
              <span className="rounded-full bg-indigo-600 px-1.5 py-0.2 text-[9px] font-bold text-white">
                {processed.clusteredCount} hidden
              </span>
            )}
          </button>

          {/* Layout Mode Switcher */}
          <div className="flex items-center rounded-xl border border-slate-200 bg-slate-100/60 p-0.5 dark:border-slate-700 dark:bg-slate-800/60">
            <button
              type="button"
              onClick={() => setLayoutMode("flow")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium transition-all ${
                layoutMode === "flow"
                  ? "bg-white text-ink shadow-sm dark:bg-slate-700"
                  : "text-slate-500 hover:text-ink"
              }`}
              title="Directed Flow Layout (Hierarchical Left-to-Right)"
            >
              <Workflow size={12} />
              <span>Flow</span>
            </button>
            <button
              type="button"
              onClick={() => setLayoutMode("radial")}
              className={`flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium transition-all ${
                layoutMode === "radial"
                  ? "bg-white text-ink shadow-sm dark:bg-slate-700"
                  : "text-slate-500 hover:text-ink"
              }`}
              title="Radial Orbit Layout (Concentric Hub & Spoke)"
            >
              <Orbit size={12} />
              <span>Radar</span>
            </button>
          </div>

          {/* Min Amount Dust Filter */}
          <div className="flex items-center gap-1">
            <span className="text-[11px] font-medium text-slate-400 hidden sm:inline">Min:</span>
            <select
              value={minAmount}
              onChange={(e) => setMinAmount(Number(e.target.value))}
              className="rounded-xl border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-ink shadow-sm focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              aria-label="Filter minimum amount"
            >
              <option value={0}>All Amounts</option>
              <option value={0.0001}>≥ 0.0001 BTC</option>
              <option value={0.001}>≥ 0.001 BTC</option>
              <option value={0.01}>≥ 0.01 BTC</option>
              <option value={0.1}>≥ 0.1 BTC</option>
            </select>
          </div>

          {/* Flagged Only Toggle */}
          <button
            type="button"
            onClick={() => setFlaggedOnly(!flaggedOnly)}
            className={`flex items-center gap-1 rounded-xl border px-2 py-1 text-xs font-semibold transition-all ${
              flaggedOnly
                ? "border-rose-400 bg-rose-50 text-rose-700 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-300"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            }`}
            title="Show only flagged or suspicious entities"
          >
            <ShieldAlert size={12} className={flaggedOnly ? "text-rose-600" : "text-slate-400"} />
            <span>Threats Only</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Quick Node Search inside Graph */}
          <form onSubmit={handleSearchNode} className="relative hidden md:block">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Find node..."
              className="w-32 rounded-xl border border-slate-200 bg-slate-50 py-1 pl-7 pr-2 text-xs text-ink transition-all focus:w-44 focus:outline-none focus:ring-1 focus:ring-primary dark:border-slate-700 dark:bg-slate-800"
            />
          </form>

          {/* View Reset */}
          <button
            type="button"
            onClick={() => reactFlowInstance.fitView({ padding: 0.25, duration: 400 })}
            className="flex h-7 w-7 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            title="Fit to view"
          >
            <Maximize2 size={13} />
          </button>

          {/* Export Buttons */}
          <Button variant="secondary" size="sm" onClick={() => void exportPng()} className="h-7 text-xs px-2.5">
            <Download size={12} className="mr-1" /> PNG
          </Button>
          <Button variant="secondary" size="sm" onClick={exportJson} className="h-7 text-xs px-2.5">
            <Download size={12} className="mr-1" /> JSON
          </Button>
        </div>
      </div>

      {/* Main Canvas Container */}
      <div className="relative">
        <div
          ref={setContainer}
          style={{ height: minHeight }}
          className="relative overflow-hidden rounded-2xl border border-slate-200 bg-surface shadow-inner dark:border-slate-800"
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            onPaneClick={() => setSelectedNode(null)}
            fitView
            fitViewOptions={{ padding: 0.25 }}
            minZoom={0.15}
            maxZoom={2.2}
            proOptions={{ hideAttribution: true }}
            nodesDraggable
            nodesConnectable={false}
          >
            <Background
              color={isDark ? "#1E293B" : "#E2E8F0"}
              gap={24}
              size={1.5}
            />
            <Controls
              showInteractive={false}
              position="bottom-left"
              className="!border-slate-200 !bg-white/90 !shadow-lg dark:!border-slate-800 dark:!bg-slate-900/90"
            />
            <MiniMap
              pannable
              zoomable
              style={{
                borderRadius: 12,
                border: isDark ? "1px solid #1E293B" : "1px solid #E2E8F0",
                backgroundColor: isDark ? "#0F172A" : "#FFFFFF",
              }}
              maskColor={isDark ? "rgba(15, 23, 42, 0.65)" : "rgba(241, 245, 249, 0.65)"}
              nodeColor={(node) => {
                if (node.id === graph.focus_address) return "#2563EB";
                if (node.type === "cluster") return "#6366F1";
                const d = node.data as unknown as CustomNodeData;
                return GRAPH_NODE_COLORS[d.type]?.border ?? "#94A3B8";
              }}
            />
          </ReactFlow>

          {/* Interactive Entity Inspector Panel */}
          <EntityInspector
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onSetFocus={(addr) => {
              if (onSetFocus) onSetFocus(addr);
              setSelectedNode(null);
            }}
            onTraceFromHere={(addr) => {
              if (onTraceFromHere) onTraceFromHere(addr);
              setSelectedNode(null);
            }}
            onExpandCluster={(clusterId) => {
              handleExpandCluster(clusterId);
              setSelectedNode(null);
            }}
          />

          {/* Floating Simplification Summary Pill */}
          {processed.clusteredCount > 0 && clusterLeaves && (
            <div className="pointer-events-none absolute bottom-3 left-16 z-10 flex items-center gap-1.5 rounded-full border border-indigo-200/80 bg-white/95 px-3 py-1 text-[11px] font-semibold text-indigo-700 shadow-md backdrop-blur dark:border-indigo-800 dark:bg-slate-900/95 dark:text-indigo-300">
              <Sparkles size={12} className="text-indigo-500" />
              <span>
                Simplified: {processed.nodes.length} nodes ({processed.clusteredCount} minor senders clustered)
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function GraphCanvas(props: GraphCanvasProps) {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
