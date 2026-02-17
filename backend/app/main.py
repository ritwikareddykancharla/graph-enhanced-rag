"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.graph import router as graph_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    print("Starting up Graph-Enhanced RAG application...")

    # Initialize database tables
    try:
        await init_db()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database tables: {e}")

    yield

    # Shutdown
    print("Shutting down Graph-Enhanced RAG application...")


# Create FastAPI application
app = FastAPI(
    title="Graph-Enhanced RAG",
    description="""
A Knowledge Graph Construction Engine that ingests unstructured documents and 
autonomously builds a Knowledge Graph inside Postgres to capture relationships between entities.

## Features

- **Extraction**: Uses LangChain with OpenAI GPT-4 to extract entities and relations from text
- **Storage**: Utilizes Recursive CTEs in Postgres for efficient graph traversal
- **Querying**: Answer questions like "If Node X goes down, what features are impacted?"

## Authentication

All API endpoints require an API key passed in the `X-API-Key` header.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
cors_origins = (
    ["*"]
    if settings.cors_allow_origins.strip() == "*"
    else [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(graph_router)
