"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database import init_db, check_db_connection
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.graph import router as graph_router

settings = get_settings()

STATIC_DIR = Path(__file__).parent / "static"


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(graph_router)

# Mount static files for React frontend (must be after API routes)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/", include_in_schema=False)
async def root():
    """Serve React app or redirect to docs"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")


@app.get("/{path:path}", include_in_schema=False)
async def serve_spa(path: str):
    """Serve React app for client-side routing"""
    file_path = STATIC_DIR / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"detail": "Not found"})
