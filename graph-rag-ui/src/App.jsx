import { useState, useEffect, useCallback } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import GraphFlow from './components/GraphFlow';
import InputPanel from './components/InputPanel';
import { getNodes, getEdges } from './services/api';

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [impactedNodeIds, setImpactedNodeIds] = useState([]);
  const [sourceNodeId, setSourceNodeId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  const fetchGraph = useCallback(async () => {
    try {
      const [nodesData, edgesData] = await Promise.all([getNodes(), getEdges()]);
      setNodes(nodesData.nodes || []);
      setEdges(edgesData.edges || []);
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to fetch graph:', error);
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const handleGraphUpdate = useCallback(() => {
    fetchGraph();
    setImpactedNodeIds([]);
    setSourceNodeId(null);
  }, [fetchGraph]);

  const handleImpactResult = useCallback((result) => {
    if (result) {
      const impactedIds = result.impacted_nodes.map((n) => n.id);
      setImpactedNodeIds(impactedIds);
      setSourceNodeId(result.source_node_id);
    } else {
      setImpactedNodeIds([]);
      setSourceNodeId(null);
    }
  }, []);

  return (
    <ReactFlowProvider>
      <div className="h-screen w-screen flex bg-slate-900">
        <div className="w-96 min-w-96 border-r border-slate-700 flex-shrink-0">
          <InputPanel
            onGraphUpdate={handleGraphUpdate}
            onImpactResult={handleImpactResult}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        </div>
        <div className="flex-1 flex flex-col">
          <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center px-4 justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-white font-medium">Knowledge Graph</h2>
              <span className="text-slate-400 text-sm">
                {nodes.length} nodes, {edges.length} edges
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-slate-400 text-sm">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          <div className="flex-1">
            {nodes.length === 0 ? (
              <div className="h-full flex items-center justify-center bg-slate-900">
                <div className="text-center text-slate-400">
                  <svg
                    className="mx-auto h-16 w-16 mb-4 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
                    />
                  </svg>
                  <p className="text-lg font-medium">No graph data</p>
                  <p className="text-sm mt-1">
                    Paste text in the left panel to build your knowledge graph
                  </p>
                </div>
              </div>
            ) : (
              <GraphFlow
                nodes={nodes}
                edges={edges}
                impactedNodeIds={impactedNodeIds}
                sourceNodeId={sourceNodeId}
              />
            )}
          </div>
          {impactedNodeIds.length > 0 && (
            <div className="h-12 bg-red-900/50 border-t border-red-700 flex items-center px-4">
              <span className="text-red-300 text-sm font-medium">
                Impact Analysis: {impactedNodeIds.length} node(s) affected (shown in red)
              </span>
            </div>
          )}
        </div>
      </div>
    </ReactFlowProvider>
  );
}

export default App;
