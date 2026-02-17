import { useState } from 'react';
import { ingestText, ingestUrl, analyzeImpact } from '../services/api';
import { demoGraph } from '../data/demoGraph';

const EXAMPLE_TEXT = `The Payment Service depends on Database A. Database A is hosted on AWS. The Fraud Team owns the Payment Service. Database A connects to Cache B for session storage. The Notification Service uses the Payment Service for transactions.`;

export default function InputPanel({
  onGraphUpdate,
  onImpactResult,
  isLoading,
  setIsLoading,
  demoMode,
  onToggleDemo,
}) {
  const [mode, setMode] = useState('text');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [impactNode, setImpactNode] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });

  const handleIngest = async () => {
    if (demoMode) {
      setText(demoGraph.text);
      onGraphUpdate();
      setStatus({
        type: 'info',
        message: 'Demo mode is on. Using sample graph data.',
      });
      return;
    }

    if (mode === 'text' && !text.trim()) {
      setStatus({ type: 'error', message: 'Paste some text to ingest.' });
      return;
    }
    if (mode === 'url' && !url.trim()) {
      setStatus({ type: 'error', message: 'Add a URL to ingest.' });
      return;
    }

    setIsLoading(true);
    setStatus({ type: 'info', message: 'Extracting entities and relations…' });

    try {
      const result =
        mode === 'text' ? await ingestText(text) : await ingestUrl(url);
      setStatus({
        type: 'success',
        message: `Extracted ${result.entities_extracted} entities and ${result.relations_extracted} relations.`,
      });
      onGraphUpdate();
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to process input.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImpactAnalysis = async () => {
    if (!impactNode.trim()) {
      setStatus({ type: 'error', message: 'Enter a node name to analyze.' });
      return;
    }

    setIsLoading(true);
    setStatus({ type: 'info', message: `Tracing impact for "${impactNode}"…` });

    try {
      const result = await analyzeImpact(impactNode);
      setStatus({
        type: 'success',
        message: `Found ${result.total_impacted} impacted nodes.`,
      });
      onImpactResult(result);
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Impact analysis failed.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadExample = () => {
    setMode('text');
    setText(EXAMPLE_TEXT);
  };

  const clearImpact = () => {
    onImpactResult(null);
    setStatus({ type: 'info', message: 'Impact highlighting cleared.' });
  };

  return (
    <section className="panel">
      <div className="mb-4">
        <h3>Ingestion Console</h3>
        <p>
          Feed in architecture notes or documentation. We extract entities, then
          build and traverse the knowledge graph.
        </p>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        <button
          className={`btn ${mode === 'text' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setMode('text')}
          disabled={isLoading}
        >
          Paste Text
        </button>
        <button
          className={`btn ${mode === 'url' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setMode('url')}
          disabled={isLoading}
        >
          Use URL
        </button>
        <button
          className={`btn ${demoMode ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => onToggleDemo(!demoMode)}
          disabled={isLoading}
        >
          {demoMode ? 'Demo Mode: On' : 'Demo Mode'}
        </button>
        <button className="btn btn-outline ml-auto" onClick={loadExample} disabled={isLoading}>
          Load Example
        </button>
      </div>

      {mode === 'text' ? (
        <div className="field">
          <label>Architecture Text</label>
          <textarea
            rows={7}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your system description, runbooks, or product specs..."
          />
        </div>
      ) : (
        <div className="field">
          <label>Documentation URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://your-docs.example.com/architecture"
          />
        </div>
      )}

      <button className="btn btn-primary w-full" onClick={handleIngest} disabled={isLoading}>
        {demoMode ? 'Load Demo Graph' : isLoading ? 'Processing…' : 'Build Graph'}
      </button>

      <div className="mt-6">
        <h3>Impact Analysis</h3>
        <p>Identify blast radius for any node by name.</p>
      </div>

      <div className="field mt-3">
        <label>Node Name</label>
        <input
          type="text"
          value={impactNode}
          onChange={(e) => setImpactNode(e.target.value)}
          placeholder="Database A"
        />
      </div>

      <div className="flex gap-2">
        <button className="btn btn-secondary w-full" onClick={handleImpactAnalysis} disabled={isLoading}>
          Analyze Impact
        </button>
        <button className="btn btn-outline w-full" onClick={clearImpact} disabled={isLoading}>
          Clear
        </button>
      </div>

      {status.message && (
        <div
          className={`status-pill mt-4 ${
            status.type === 'success'
              ? 'status-success'
              : status.type === 'error'
              ? 'status-error'
              : 'status-info'
          }`}
        >
          {status.message}
        </div>
      )}

      <div className="mt-6 text-xs text-[color:var(--muted)]">
        Extraction uses your configured LLM. The graph is persisted in Postgres and
        queried with recursive CTEs.
      </div>
    </section>
  );
}
