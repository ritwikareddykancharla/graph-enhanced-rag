import { useState } from 'react';
import { ingestText, analyzeImpact } from '../services/api';

const EXAMPLE_TEXT = `The Payment Service depends on Database A. Database A is hosted on AWS. The Fraud Team is responsible for the Payment Service. Database A connects to Cache B for session storage. The Notification Service uses the Payment Service for transactions.`;

export default function InputPanel({ onGraphUpdate, onImpactResult, isLoading, setIsLoading }) {
  const [text, setText] = useState('');
  const [impactNode, setImpactNode] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });

  const handleIngest = async () => {
    if (!text.trim()) {
      setStatus({ type: 'error', message: 'Please enter some text to ingest' });
      return;
    }

    setIsLoading(true);
    setStatus({ type: 'info', message: 'Processing text and extracting entities...' });

    try {
      const result = await ingestText(text);
      setStatus({
        type: 'success',
        message: `Extracted ${result.entities_extracted} entities and ${result.relations_extracted} relations`,
      });
      onGraphUpdate();
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to process text',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImpactAnalysis = async () => {
    if (!impactNode.trim()) {
      setStatus({ type: 'error', message: 'Please enter a node name to analyze' });
      return;
    }

    setIsLoading(true);
    setStatus({ type: 'info', message: `Analyzing impact for "${impactNode}"...` });

    try {
      const result = await analyzeImpact(impactNode);
      setStatus({
        type: 'success',
        message: `Found ${result.total_impacted} impacted nodes`,
      });
      onImpactResult(result);
    } catch (error) {
      setStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to analyze impact',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadExample = () => {
    setText(EXAMPLE_TEXT);
  };

  const clearGraph = async () => {
    onImpactResult(null);
    setStatus({ type: 'info', message: 'Graph cleared. Ingest new text to build a graph.' });
  };

  return (
    <div className="h-full flex flex-col p-6 bg-slate-800 text-white overflow-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-2">Knowledge Graph Builder</h1>
        <p className="text-slate-400 text-sm">
          Paste text to extract entities and build a visual graph
        </p>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-slate-300">Input Text</label>
          <button
            onClick={loadExample}
            className="text-xs text-blue-400 hover:text-blue-300 underline"
          >
            Load Example
          </button>
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your architecture documentation or system description here..."
          className="w-full h-40 p-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
        <button
          onClick={handleIngest}
          disabled={isLoading}
          className="w-full mt-3 py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {isLoading ? 'Processing...' : 'Build Graph'}
        </button>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          Impact Analysis
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={impactNode}
            onChange={(e) => setImpactNode(e.target.value)}
            placeholder="Enter node name (e.g., Database A)"
            className="flex-1 p-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleImpactAnalysis}
            disabled={isLoading}
            className="py-3 px-4 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors whitespace-nowrap"
          >
            Analyze Impact
          </button>
        </div>
        <button
          onClick={clearGraph}
          className="w-full mt-2 py-2 px-4 bg-slate-600 hover:bg-slate-500 text-white text-sm rounded-lg transition-colors"
        >
          Clear Impact Highlighting
        </button>
      </div>

      {status.message && (
        <div
          className={`p-3 rounded-lg text-sm ${
            status.type === 'error'
              ? 'bg-red-900/50 text-red-300 border border-red-700'
              : status.type === 'success'
              ? 'bg-green-900/50 text-green-300 border border-green-700'
              : 'bg-blue-900/50 text-blue-300 border border-blue-700'
          }`}
        >
          {status.message}
        </div>
      )}

      <div className="mt-auto pt-6 border-t border-slate-700">
        <h3 className="text-sm font-medium text-slate-300 mb-2">How it works</h3>
        <ul className="text-xs text-slate-400 space-y-1">
          <li>• LLM extracts entities and relationships from text</li>
          <li>• Graph is stored in Postgres with recursive CTEs</li>
          <li>• Impact analysis traverses the graph to find dependencies</li>
        </ul>
      </div>
    </div>
  );
}
