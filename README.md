# Graph-Enhanced RAG

A Knowledge Graph Construction Engine that ingests unstructured documents and autonomously builds a Knowledge Graph inside Postgres to capture relationships between entities. Standard RAG struggles with multi-hop reasoning - this system solves that by using graph traversal for complex queries.

## Features

- **Extraction**: Uses LangChain with OpenAI GPT-4 to extract entities and relations (e.g., `Server A → depends_on → Database B`) from raw text or web content.
- **Storage**: Utilizes Recursive CTEs in Postgres to traverse the graph efficiently without a separate graph database.
- **Querying**: Answer questions like "If Node X goes down, what features are impacted?" by traversing the graph structure.
- **Multi-source Ingestion**: Raw text API and URL scraping support.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python FastAPI |
| Database | Postgres (Railway) |
| LLM Framework | LangChain |
| Default LLM | OpenAI GPT-4 |
| Authentication | API Key |
| Deployment | Railway |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  API Layer                                                   │
│  ├── /ingest/text     - Raw text ingestion                  │
│  ├── /ingest/url      - URL scraping & ingestion            │
│  ├── /graph/entities  - Entity CRUD                         │
│  ├── /graph/relations - Relation CRUD                       │
│  ├── /query/impact    - "What if X goes down?"              │
│  └── /query/path      - Path finding between nodes          │
├─────────────────────────────────────────────────────────────┤
│  Services                                                    │
│  ├── ExtractionService - LangChain entity/relation extraction│
│  ├── GraphService      - Recursive CTE traversal            │
│  └── IngestionService  - Document processing pipeline       │
├─────────────────────────────────────────────────────────────┤
│  Database: Postgres (Railway)                               │
│  ├── nodes table        - Entities with metadata            │
│  ├── edges table        - Relations with types/weights      │
│  └── documents table    - Source document tracking          │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
graph-enhanced-rag/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings via Pydantic
│   ├── database.py             # Async Postgres connection
│   ├── auth.py                 # API Key middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── db_models.py        # SQL table definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extraction.py       # LangChain entity extraction
│   │   ├── graph.py            # Recursive CTE operations
│   │   └── ingestion.py        # Document ingestion pipeline
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ingest.py           # Ingestion endpoints
│   │   ├── graph.py            # Graph query endpoints
│   │   └── health.py           # Health check
│   └── utils/
│       ├── __init__.py
│       └── url_scraper.py      # Web scraping utility
├── tests/
│   ├── conftest.py
│   ├── test_extraction.py
│   ├── test_graph.py
│   └── test_api.py
├── requirements.txt
├── pyproject.toml
├── .env.example
├── Procfile                    # Railway deployment
├── runtime.txt
└── README.md
```

## Database Schema

### Nodes (Entities)

```sql
CREATE TABLE nodes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),           -- e.g., 'server', 'database', 'service'
    properties JSONB DEFAULT '{}',
    source_document_id INTEGER REFERENCES documents(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Edges (Relations)

```sql
CREATE TABLE edges (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES nodes(id),
    target_id INTEGER REFERENCES nodes(id),
    relation_type VARCHAR(100) NOT NULL,  -- e.g., 'depends_on', 'connects_to'
    properties JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient traversal
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_nodes_name ON nodes(name);
```

### Documents

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source_type VARCHAR(50),     -- 'text' or 'url'
    source_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Recursive CTE for Impact Analysis

The core graph traversal uses Postgres Recursive CTEs:

```sql
-- Find all impacted nodes if node X goes down
WITH RECURSIVE impacted AS (
    -- Base case: direct dependents
    SELECT target_id, relation_type, 1 as depth
    FROM edges WHERE source_id = :node_id
    
    UNION ALL
    
    -- Recursive: find dependents of dependents
    SELECT e.target_id, e.relation_type, i.depth + 1
    FROM edges e
    JOIN impacted i ON e.source_id = i.target_id
    WHERE i.depth < :max_depth
)
SELECT n.name, n.type, i.relation_type, i.depth
FROM impacted i
JOIN nodes n ON n.id = i.target_id
ORDER BY i.depth;
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest/text` | POST | Ingest raw text, extract entities/relations |
| `/ingest/url` | POST | Scrape URL, extract entities/relations |
| `/graph/nodes` | GET/POST | List/create nodes |
| `/graph/nodes/{id}` | GET/DELETE | Get/delete node |
| `/graph/edges` | GET/POST | List/create edges |
| `/graph/edges/{id}` | GET/DELETE | Get/delete edge |
| `/query/impact` | POST | Find all impacted nodes given a node ID |
| `/query/path` | POST | Find path between two nodes |
| `/query/search` | GET | Search nodes by name/type |

### Example Requests

#### Ingest Raw Text

```bash
curl -X POST "https://your-app.railway.app/ingest/text" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Server A depends on Database B. Database B connects to Cache C. The Payment Service uses Server A.",
    "metadata": {"source": "architecture-doc"}
  }'
```

#### Ingest from URL

```bash
curl -X POST "https://your-app.railway.app/ingest/url" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.example.com/architecture",
    "metadata": {"project": "my-project"}
  }'
```

#### Query Impact Analysis

```bash
curl -X POST "https://your-app.railway.app/query/impact" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": 1,
    "max_depth": 5
  }'
```

Response:
```json
{
  "impacted_nodes": [
    {"name": "Payment Service", "type": "service", "relation": "uses", "depth": 1},
    {"name": "Database B", "type": "database", "relation": "depends_on", "depth": 2}
  ]
}
```

#### Find Path Between Nodes

```bash
curl -X POST "https://your-app.railway.app/query/path" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "source_node_id": 1,
    "target_node_id": 5,
    "max_depth": 10
  }'
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# LLM Configuration
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai           # openai, anthropic, ollama
LLM_MODEL=gpt-4               # gpt-4, gpt-3.5-turbo, claude-3-opus

# API Authentication
API_KEY=your-secure-api-key

# Optional
MAX_TRAVERSAL_DEPTH=5         # Default max depth for graph queries
```

## Local Development

### Prerequisites

- Python 3.11+
- Postgres 14+
- Virtual environment

### Setup

```bash
# Clone the repository
git clone git@github.com:ritwikareddykancharla/graph-enhanced-rag.git
cd graph-enhanced-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your values

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## Railway Deployment

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)

### Manual Deploy

1. Create a new project on Railway
2. Add a Postgres database
3. Deploy from GitHub repo
4. Set environment variables:
   - `OPENAI_API_KEY`
   - `API_KEY`
   - `DATABASE_URL` (auto-populated from Postgres addon)

### Railway Configuration

**Procfile:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**runtime.txt:**
```
python-3.11.0
```

## Implementation Phases

| Phase | Status | Tasks |
|-------|--------|-------|
| **1. Foundation** | Pending | Project setup, database models, async connection, config |
| **2. Core Services** | Pending | Extraction service with LangChain, Graph service with CTEs |
| **3. API Endpoints** | Pending | Ingestion APIs, Query APIs, API Key auth |
| **4. URL Scraping** | Pending | Web content extraction, text cleaning |
| **5. Testing** | Pending | Unit tests, integration tests |
| **6. Deployment** | Pending | Railway config, Procfile, documentation |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_graph.py -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.
