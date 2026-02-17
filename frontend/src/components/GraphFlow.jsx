import { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const nodeTypeColors = {
  server: '#f59e0b',
  database: '#10b981',
  service: '#ef7a3f',
  api: '#8b5cf6',
  cache: '#3b82f6',
  default: '#9ca3af',
};

const createNodeStyle = (type, isImpacted, isSource) => {
  const baseColor = nodeTypeColors[type] || nodeTypeColors.default;
  return {
    background: isImpacted ? '#ef4444' : baseColor,
    color: '#0b0b0b',
    border: isSource ? '2px solid #f7f3ea' : '1px solid rgba(255,255,255,0.6)',
    borderRadius: '14px',
    padding: '10px 14px',
    fontSize: '13px',
    fontWeight: '600',
    fontFamily: '"Space Grotesk", system-ui, sans-serif',
    boxShadow: isImpacted
      ? '0 0 24px rgba(239, 68, 68, 0.45)'
      : '0 10px 28px rgba(0,0,0,0.28)',
    transition: 'all 0.3s ease',
  };
};

export default function GraphFlow({ nodes: propNodes, edges: propEdges, impactedNodeIds = [], sourceNodeId = null }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const convertToReactFlowNodes = useCallback((apiNodes) => {
    return apiNodes.map((node, index) => {
      const isImpacted = impactedNodeIds.includes(node.id);
      const isSource = node.id === sourceNodeId;
      const angle = (index / apiNodes.length) * 2 * Math.PI;
      const radius = 220;
      
      return {
        id: String(node.id),
        type: 'default',
        data: {
          label: (
            <div className="flex flex-col items-center">
              <span>{node.name}</span>
              {node.type && (
                <span className="text-[11px] uppercase tracking-[0.2em] mt-1 opacity-70">
                  {node.type}
                </span>
              )}
            </div>
          ),
        },
        position: {
          x: 320 + radius * Math.cos(angle),
          y: 280 + radius * Math.sin(angle),
        },
        style: createNodeStyle(node.type, isImpacted, isSource),
      };
    });
  }, [impactedNodeIds, sourceNodeId]);

  const convertToReactFlowEdges = useCallback((apiEdges) => {
    return apiEdges.map((edge) => ({
      id: String(edge.id),
      source: String(edge.source_id),
      target: String(edge.target_id),
      label: edge.relation_type,
      animated: impactedNodeIds.includes(edge.target_id),
      style: {
        stroke: impactedNodeIds.includes(edge.target_id) ? '#ef4444' : '#8b8b8b',
        strokeWidth: 2,
      },
      labelStyle: { fill: '#f7f3ea', fontWeight: 500 },
      labelBgStyle: { fill: '#151515', fillOpacity: 0.85 },
      labelBgPadding: [8, 4],
      labelBgBorderRadius: 4,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: impactedNodeIds.includes(edge.target_id) ? '#ef4444' : '#8b8b8b',
      },
    }));
  }, [impactedNodeIds]);

  useEffect(() => {
    if (propNodes && propNodes.length > 0) {
      setNodes(convertToReactFlowNodes(propNodes));
    }
  }, [propNodes, convertToReactFlowNodes, setNodes]);

  useEffect(() => {
    if (propEdges && propEdges.length > 0) {
      setEdges(convertToReactFlowEdges(propEdges));
    }
  }, [propEdges, convertToReactFlowEdges, setEdges]);

  const nodeTypes = useMemo(() => ({}), []);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="rgba(255,255,255,0.08)" gap={24} />
        <Controls className="bg-[#1a1a1a] border-[color:rgba(255,255,255,0.08)]" />
        <MiniMap
          className="bg-[#1a1a1a] border-[color:rgba(255,255,255,0.08)]"
          nodeColor={(node) => node.style?.background || '#6b7280'}
          maskColor="rgba(0, 0, 0, 0.65)"
        />
      </ReactFlow>
    </div>
  );
}
