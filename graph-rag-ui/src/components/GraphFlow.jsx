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
  server: '#3b82f6',
  database: '#10b981',
  service: '#8b5cf6',
  cache: '#f59e0b',
  default: '#6b7280',
};

const createNodeStyle = (type, isImpacted, isSource) => {
  const baseColor = nodeTypeColors[type] || nodeTypeColors.default;
  return {
    background: isImpacted ? '#ef4444' : baseColor,
    color: 'white',
    border: isSource ? '3px solid #fbbf24' : '2px solid white',
    borderRadius: '8px',
    padding: '10px 15px',
    fontSize: '14px',
    fontWeight: '600',
    boxShadow: isImpacted ? '0 0 20px rgba(239, 68, 68, 0.5)' : '0 2px 8px rgba(0,0,0,0.2)',
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
      const radius = 200;
      
      return {
        id: String(node.id),
        type: 'default',
        data: {
          label: (
            <div className="flex flex-col items-center">
              <span>{node.name}</span>
              {node.type && (
                <span className="text-xs opacity-75 mt-1">{node.type}</span>
              )}
            </div>
          ),
        },
        position: {
          x: 300 + radius * Math.cos(angle),
          y: 300 + radius * Math.sin(angle),
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
        stroke: impactedNodeIds.includes(edge.target_id) ? '#ef4444' : '#94a3b8',
        strokeWidth: 2,
      },
      labelStyle: { fill: '#fff', fontWeight: 500 },
      labelBgStyle: { fill: '#1e293b', fillOpacity: 0.8 },
      labelBgPadding: [8, 4],
      labelBgBorderRadius: 4,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: impactedNodeIds.includes(edge.target_id) ? '#ef4444' : '#94a3b8',
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
    <div className="w-full h-full bg-slate-900">
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
        <Background color="#334155" gap={20} />
        <Controls className="bg-slate-800 border-slate-700" />
        <MiniMap
          className="bg-slate-800 border-slate-700"
          nodeColor={(node) => node.style?.background || '#6b7280'}
          maskColor="rgba(0, 0, 0, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
