# Architecture Deep Dive

## Overview

Graph-Enhanced RAG is a **knowledge-graph-first RAG system** that transforms unstructured text into a queryable knowledge graph stored in PostgreSQL. Unlike traditional RAG systems that rely solely on vector similarity, this system extracts structured entities and relationships, enabling multi-hop reasoning and impact analysis.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Graph-Enhanced RAG                                 │
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────┐ │
│   │   Text/URL  │ ──► │     LLM     │ ──► │  Postgres   │ ──► │  Query  │ │
│   │   Input     │     │ Extraction  │     │   Graph     │     │ Engine  │ │
│   └─────────────┘     └─────────────┘     └─────────────┘     └─────────┘ │
│                                                                     │       │
│   Unstructured          Entities +         Nodes + Edges      Recursive │
│   Documents             Relations          with Types          CTEs      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌────────────┐    ┌──────────────────────────────────────────────────────┐  │
│  │  Frontend  │    │                      Backend                         │  │
│  │  (React)   │    │                      (FastAPI)                       │  │
│  │            │    │                                                      │  │
│  │ ┌────────┐ │    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │ │ Graph  │ │    │  │    API      │  │  Services   │  │    Utils    │  │  │
│  │ │ Studio │ │    │  │   Layer     │  │             │  │             │  │  │
│  │ │   UI   │ │    │  │             │  │ ┌─────────┐ │  │ ┌─────────┐ │  │  │
│  │ └────────┘ │    │  │ /ingest/*  │──┼─┼►Extract │ │  │ │Normalize│ │  │  │
│  │            │    │  │ /graph/*   │  │ │Service  │ │  │ │  Utils  │ │  │  │
│  │ ┌────────┐ │    │  │ /health    │  │ └─────────┘ │  │ └─────────┘ │  │  │
│  │ │ Input  │ │    │  │             │  │ ┌─────────┐ │  │ ┌─────────┐ │  │  │
│  │ │ Panel  │ │    │  │             │  │ │ Graph   │ │  │ │  Retry  │ │  │  │
│  │ └────────┘ │    │  │             │──┼─┼►Service │ │  │ │  Logic  │ │  │  │
│  │            │    │  │             │  │ └─────────┘ │  │ └─────────┘ │  │  │
│  │ ┌────────┐ │    │  │             │  │ ┌─────────┐ │  │ ┌─────────┐ │  │  │
│  │ │Impact  │ │    │  │             │  │ │Ingest   │ │  │ │  Rate   │ │  │  │
│  │ │Query   │ │    │  │             │──┼─┼►Service │ │  │ │ Limiter │ │  │  │
│  │ └────────┘ │    │  │             │  │ └─────────┘ │  │ └─────────┘ │  │  │
│  │            │    │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └────────────┘    └──────────────────────────┬───────────────────────────┘  │
│                                                   │                            │
│                                                   ▼                            │
│                                          ┌───────────────┐                    │
│                                          │   PostgreSQL  │                    │
│                                          │               │                    │
│                                          │  ┌─────────┐  │                    │
│                                          │  │ nodes   │  │                    │
│                                          │  ├─────────┤  │                    │
│                                          │  │ edges   │  │                    │
│                                          │  ├─────────┤  │                    │
│                                          │  │documents│  │                    │
│                                          │  └─────────┘  │                    │
│                                          └───────────────┘                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19 + Vite + Tailwind CSS | Interactive graph visualization |
| Graph Rendering | @xyflow/react (ReactFlow) | Node-edge canvas with zoom/pan |
| Backend | FastAPI + Uvicorn | Async REST API |
| LLM Integration | LangChain + OpenAI GPT-4 | Entity/relation extraction |
| Database | PostgreSQL + SQLAlchemy (async) | Graph storage with recursive CTEs |
| Deployment | Railway (Railpack) | Single-service monorepo deployment |

---

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory, CORS, middleware
│   ├── config.py            # Pydantic settings from environment
│   ├── database.py          # Async SQLAlchemy engine, session management
│   ├── auth.py              # API key validation
│   ├── api/
│   │   ├── health.py        # /health endpoint
│   │   ├── ingest.py        # /ingest/text, /ingest/url endpoints
│   │   └── graph.py         # /graph/* CRUD and query endpoints
│   ├── models/
│   │   ├── db_models.py     # SQLAlchemy Node, Edge, Document models
│   │   └── schemas.py       # Pydantic request/response schemas
│   ├── services/
│   │   ├── extraction.py    # LLM-based entity/relation extraction
│   │   ├── ingestion.py     # Ingestion pipeline orchestrator
│   │   └── graph.py         # Graph operations and traversal
│   ├── utils/
│   │   ├── normalization.py # Entity name/type canonicalization
│   │   ├── logging_config.py# Structured JSON logging
│   │   ├── rate_limit.py    # In-memory rate limiting middleware
│   │   └── retry.py         # Async retry with exponential backoff
│   └── static/              # Static file serving (for SPA fallback)
├── tests/                   # Pytest test suite
├── evals/                   # Labeled evaluation datasets
├── scripts/                 # Evaluation and utility scripts
├── requirements.txt
├── pyproject.toml
└── .env.example
```

### Core Services

#### 1. Extraction Service (`services/extraction.py`)

The extraction service uses LangChain with OpenAI GPT-4 to extract structured entities and relations from unstructured text.

**Process Flow:**
```
Input Text → Prompt Template → LLM Call → JSON Parsing → ExtractionResult
```

**Key Components:**

- **Prompt Engineering**: Two-stage prompts with fallback for robustness
  - Primary: Structured extraction prompt with explicit JSON schema
  - Fallback: Format instructions via PydanticOutputParser

- **Output Parsing**: Handles various LLM response formats
  - Markdown code blocks (` ```json ... ``` `)
  - Plain JSON extraction via regex
  - Graceful fallback to empty result on failure

**Example Extraction:**

```python
# Input
text = "The Payment Service depends on Database X for transaction storage."

# Output (ExtractionResult)
{
    "entities": [
        {"name": "Payment Service", "type": "service"},
        {"name": "Database X", "type": "database"}
    ],
    "relations": [
        {"source": "Payment Service", "target": "Database X", "relation_type": "depends_on"}
    ]
}
```

#### 2. Graph Service (`services/graph.py`)

The graph service manages all database operations for nodes and edges, including advanced traversal using PostgreSQL Recursive CTEs.

**Node Operations:**
- `create_node()` - Insert new entity
- `get_or_create_node()` - Upsert with normalization
- `find_node_by_normalized_name()` - Fuzzy matching with aliases

**Edge Operations:**
- `create_edge()` - Insert new relationship
- `list_edges()` - Paginated with filters

**Graph Traversal (The Core Innovation):**

##### Impact Analysis (`get_impacted_nodes`)

Finds all nodes affected by a source node using recursive dependency traversal.

```sql
WITH RECURSIVE impacted AS (
    -- Base case: direct dependents
    SELECT e.target_id, e.relation_type, 1 as depth, ARRAY[n.name] as path
    FROM edges e
    JOIN nodes n ON n.id = e.target_id
    WHERE e.source_id = :node_id
    
    UNION ALL
    
    -- Recursive case: transitive dependents
    SELECT e.target_id, e.relation_type, i.depth + 1, i.path || n.name
    FROM edges e
    JOIN impacted i ON e.source_id = i.target_id
    JOIN nodes n ON n.id = e.target_id
    WHERE i.depth < :max_depth
)
SELECT * FROM impacted ORDER BY depth, name;
```

**Use Case:** "If the Auth Service goes down, what features are impacted?"
- Returns cascading dependency chain with depth and path

##### Path Finding (`find_path`)

Finds paths between two nodes with scoring and explanation generation.

```sql
WITH RECURSIVE path_search AS (
    -- Base case
    SELECT e.target_id, e.relation_type, 1 as depth,
           ARRAY[e.source_id, e.target_id] as path_ids,
           ARRAY[e.relation_type] as relations,
           e.weight as score
    FROM edges e WHERE e.source_id = :source_id
    
    UNION ALL
    
    -- Recursive case with cycle prevention
    SELECT e.target_id, e.relation_type, ps.depth + 1,
           ps.path_ids || e.target_id,
           ps.relations || e.relation_type,
           ps.score + e.weight
    FROM edges e
    JOIN path_search ps ON e.source_id = ps.target_id
    WHERE ps.depth < :max_depth
    AND NOT (e.target_id = ANY(ps.path_ids))  -- Prevent cycles
)
SELECT * FROM path_search WHERE target_id = :target_id ORDER BY depth;
```

**Output Enhancement:**
- Multiple paths returned with scoring
- Human-readable explanation string per path:
  ```
  "Service A -[depends_on]-> Database B -[replicates_to]-> Analytics Warehouse"
  ```

#### 3. Ingestion Service (`services/ingestion.py`)

Orchestrates the complete ingestion pipeline.

**Pipeline Steps:**
```
1. Store document text in `documents` table
2. Call ExtractionService to get entities/relations
3. Normalize entity names and types
4. Create/get nodes with deduplication
5. Create edges between nodes
6. Link nodes to source document
```

**URL Ingestion:**
- Fetches HTML content via httpx
- Extracts text with BeautifulSoup
- Follows same pipeline as text ingestion

### Data Models

#### Database Schema (`models/db_models.py`)

```sql
-- Nodes table (entities)
CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) DEFAULT 'unknown',
    properties JSONB DEFAULT '{}',
    source_document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Edges table (relationships)
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES nodes(id) NOT NULL,
    target_id INTEGER REFERENCES nodes(id) NOT NULL,
    relation_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents table (source text)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with DB status |
| `/ingest/text` | POST | Ingest raw text |
| `/ingest/url` | POST | Ingest from URL |
| `/graph/nodes` | GET | List nodes (paginated) |
| `/graph/nodes/{id}` | GET | Get single node |
| `/graph/edges` | GET | List edges (paginated) |
| `/graph/query/impact` | POST | Impact analysis from node |
| `/graph/query/path` | POST | Find path between nodes |

### Production Features

#### Rate Limiting

In-memory sliding window rate limiter per client + API key.

```python
# Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW_SECONDS=60
```

#### Request Size Guard

Middleware that rejects oversized payloads before processing.

```python
MAX_REQUEST_SIZE_BYTES=2000000  # 2MB
```

#### Retry Logic

Exponential backoff for network calls to LLM and external URLs.

```python
@retry_async(retries=3, base_delay=0.5, max_delay=5.0)
async def call_llm():
    ...
```

#### Structured Logging

JSON-formatted logs with configurable level.

```python
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # React entry point
│   ├── index.css            # Global styles + Tailwind
│   ├── components/
│   │   ├── GraphFlow.jsx    # ReactFlow canvas with nodes/edges
│   │   ├── InputPanel.jsx   # Text input, URL input, demo toggle
│   │   ├── ImpactQuery.jsx  # Impact analysis controls
│   │   └── PathQuery.jsx    # Path finding controls
│   ├── services/
│   │   └── api.js           # Axios API client
│   ├── data/
│   │   └── demoGraph.js     # Pre-seeded demo data
│   └── assets/
├── public/
├── index.html
├── package.json
├── vite.config.js
└── .env.example
```

### Key Components

#### App.jsx

Main orchestrator that:
- Manages global state (nodes, edges, impact results)
- Coordinates API connection status
- Handles demo mode toggle

#### GraphFlow.jsx

ReactFlow-based canvas that:
- Renders nodes with type-based styling
- Shows edges with relation labels
- Highlights impacted nodes during analysis
- Supports zoom, pan, and node selection

#### InputPanel.jsx

Unified input panel with:
- Text area for direct text ingestion
- URL input for web page ingestion
- Demo mode toggle for offline demonstration
- Loading states and error handling

### API Client (`services/api.js`)

Axios-based client with:
- Base URL from `VITE_API_BASE_URL`
- API key injection from `VITE_API_KEY`
- Error response normalization

---

## Graph Traversal Deep Dive

### Why Recursive CTEs?

Recursive Common Table Expressions (CTEs) in PostgreSQL provide:

1. **Performance**: Native SQL execution, no external graph DB needed
2. **Expressiveness**: Complex path queries in a single statement
3. **Composability**: Can join with other tables for enriched results
4. **No New Infrastructure**: Works with existing PostgreSQL instance

### Impact Analysis Algorithm

```
INPUT: source_node_id, max_depth
OUTPUT: List of impacted nodes with depth and path

1. Initialize impacted set with direct dependents (depth=1)
2. RECURSIVELY:
   a. For each node in impacted set at depth d
   b. Find all nodes that depend on it
   c. Add to impacted set with depth d+1
   d. Track path from source
3. Stop when max_depth reached
4. Return sorted by depth (closest impacts first)
```

### Path Finding Algorithm

```
INPUT: source_id, target_id, max_depth
OUTPUT: Multiple scored paths with explanations

1. Initialize path candidates from source's outgoing edges
2. RECURSIVELY:
   a. Extend each path candidate by one hop
   b. Prevent cycles by checking visited nodes
   c. Track cumulative weight/score
   d. Stop when target reached or max_depth exceeded
3. Score paths by (average_weight, -depth)
4. Return top-k paths with human-readable explanations
```

### Path Scoring

Paths are scored using average edge weight:

```python
score = sum(edge_weights) / path_length
```

This favors:
- Paths with stronger relations (higher weights)
- Shorter paths (normalized by length)

---

## Data Quality Controls

### Entity Normalization

Reduces duplicate entities through:

1. **Name Normalization**: Lowercase, strip whitespace, handle common variations
   ```python
   "Payment Service" → "payment_service"
   "payment-service" → "payment_service"
   ```

2. **Type Canonicalization**: Maps variants to standard types
   ```python
   "db" → "database"
   "svc" → "service"
   "api" → "api"
   ```

3. **Alias Tracking**: Stores alternative names in node properties
   ```json
   {
     "canonical_name": "payment_service",
     "aliases": ["Payment Service", "payment-svc", "PaymentSvc"]
   }
   ```

### Optional LLM Canonicalization

When `ENABLE_LLM_CANONICALIZATION=true`, the LLM also:
- Resolves entity name conflicts
- Suggests canonical names
- Merges duplicate entities

---

## Demonstration Guide

### Demo Mode (No API Required)

1. Toggle "Demo Mode" in the UI
2. Pre-seeded microservice architecture appears:
   - Payment Service
   - Auth API
   - User Database
   - Analytics Warehouse
   - Notification Service

### Live Ingestion Demo

**Sample Input:**
```
The Payment Service depends on the Auth API which connects to the User Database. 
The User Database replicates to the Analytics Warehouse for reporting. 
The Notification Service calls the Payment Service for transaction receipts.
The Analytics Dashboard queries the Analytics Warehouse.
```

**Expected Extraction:**
- 5 entities: Payment Service, Auth API, User Database, Analytics Warehouse, Notification Service, Analytics Dashboard
- 5 relations: depends_on, connects_to, replicates_to, calls, queries

### Impact Analysis Demo

1. Click on "Payment Service" node
2. Click "What's impacted?"
3. View cascading impact:
   - Depth 1: Auth API
   - Depth 2: User Database
   - Depth 3: Analytics Warehouse
   - Also: Notification Service (calls Payment Service)

### Path Finding Demo

1. Select source: "Notification Service"
2. Select target: "Analytics Warehouse"
3. Click "Find Path"
4. View result:
   ```
   Notification Service -[calls]-> Payment Service -[depends_on]-> Auth API 
   -[connects_to]-> User Database -[replicates_to]-> Analytics Warehouse
   ```

---

## Deployment Architecture

### Railway Single-Service Deployment

The application deploys as a single Railway service that builds both frontend and backend:

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Service                          │
│                                                             │
│  Build:                                                     │
│  1. pip install -r requirements.txt (Python)                │
│  2. bun install && bun run build (Frontend)                 │
│                                                             │
│  Runtime:                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  FastAPI App                         │   │
│  │                                                     │   │
│  │  /ingest/*  /graph/*  /health  →  API handlers     │   │
│  │                                                     │   │
│  │  /assets/*  /*.html  /             →  Static files │   │
│  │                                      from dist/     │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│                 ┌─────────────────┐                        │
│                 │   PostgreSQL    │                        │
│                 │   (Linked)      │                        │
│                 └─────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (auto-filled from linked Postgres) |
| `OPENAI_API_KEY` | OpenAI API key for extraction | Yes |
| `API_KEY` | API authentication key | Yes |
| `CORS_ALLOW_ORIGINS` | Allowed CORS origins | No (default: `*`) |
| `LOG_LEVEL` | Logging level | No (default: `INFO`) |
| `LLM_MODEL` | OpenAI model to use | No (default: `gpt-4`) |
| `MAX_TRAVERSAL_DEPTH` | Max graph traversal depth | No (default: `5`) |

---

## Key Innovations

### 1. Graph-First RAG

Unlike vector-only RAG, this system:
- Preserves entity relationships
- Enables multi-hop queries
- Provides explainable reasoning paths

### 2. SQL-Based Graph Engine

No Neo4j, Neptune, or specialized graph database required:
- Recursive CTEs handle all traversal
- Single PostgreSQL instance serves both storage and queries
- Easier deployment and operations

### 3. Explainable Paths

Every path query returns a human-readable explanation:
```json
{
  "explanation": "Service A -[depends_on]-> Database B -[replicates_to]-> Analytics"
}
```

### 4. Production-Ready

Built with real-world concerns:
- Rate limiting per client
- Request size validation
- Retry with exponential backoff
- Structured logging
- Graceful degradation

---

## Future Enhancements

1. **Multi-LLM Support**: Add Anthropic Claude, local models
2. **Graph Versioning**: Track changes over time
3. **Batch Ingestion**: Process multiple documents
4. **Graph Export**: Export to Neo4j, GraphML, GEXF
5. **Semantic Search**: Hybrid vector + graph queries
6. **Real-time Updates**: WebSocket for live graph updates