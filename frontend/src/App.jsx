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
      <div className="app-shell">
        <header className="app-header">
          <div>
            <div className="app-title">Graph-Enhanced RAG Studio</div>
            <div className="app-subtitle">
              Extract entities, build a knowledge graph, and trace impact paths in seconds.
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="chip">
              <span
                className={`h-2 w-2 rounded-full ${
                  isConnected ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              {isConnected ? 'API connected' : 'API offline'}
            </div>
            <div className="chip">
              {nodes.length} nodes · {edges.length} edges
            </div>
          </div>
        </header>

        <main className="main-grid">
          <InputPanel
            onGraphUpdate={handleGraphUpdate}
            onImpactResult={handleImpactResult}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />

          <section className="graph-shell">
            <div className="graph-header">
              <div className="graph-title">Live Graph Canvas</div>
              <div className="graph-stats">
                {impactedNodeIds.length > 0
                  ? `Impacting ${impactedNodeIds.length} node(s)`
                  : 'Awaiting impact analysis'}
              </div>
            </div>
            <div className="glow" />
            <div className="h-[calc(100%-56px)]">
              {nodes.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center px-6">
                  <div className="text-2xl font-semibold">No graph data yet</div>
                  <div className="mt-2 text-sm text-[color:var(--muted)] max-w-sm">
                    Drop in architecture notes or a system description to generate your
                    graph and visualize dependencies instantly.
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
          </section>
        </main>
      </div>
    </ReactFlowProvider>
  );
}

export default App;
