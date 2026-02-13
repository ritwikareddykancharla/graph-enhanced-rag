import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-key';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

export const ingestText = async (text, metadata = {}) => {
  const response = await api.post('/ingest/text', { text, metadata });
  return response.data;
};

export const ingestUrl = async (url, metadata = {}) => {
  const response = await api.post('/ingest/url', { url, metadata });
  return response.data;
};

export const getNodes = async (skip = 0, limit = 500) => {
  const response = await api.get('/graph/nodes', { params: { skip, limit } });
  return response.data;
};

export const getEdges = async (skip = 0, limit = 500) => {
  const response = await api.get('/graph/edges', { params: { skip, limit } });
  return response.data;
};

export const analyzeImpact = async (nodeName, maxDepth = 5) => {
  const response = await api.post('/graph/query/impact', {
    node_name: nodeName,
    max_depth: maxDepth,
  });
  return response.data;
};

export const findPath = async (sourceId, targetId, maxDepth = 10) => {
  const response = await api.post('/graph/query/path', {
    source_node_id: sourceId,
    target_node_id: targetId,
    max_depth: maxDepth,
  });
  return response.data;
};

export const searchNodes = async (name, type = null, limit = 50) => {
  const params = { limit };
  if (name) params.name = name;
  if (type) params.type = type;
  const response = await api.get('/graph/query/search', { params });
  return response.data;
};

export default api;
