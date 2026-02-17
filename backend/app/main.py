"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.graph import router as graph_router
from app.utils.logging_config import configure_logging
from app.utils.rate_limit import RateLimiter, RateLimitMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    configure_logging(settings.log_level)
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


# Payload size guard (before heavier middleware)
@app.middleware("http")
async def max_request_size_guard(request: Request, call_next):
    if request.headers.get("content-length"):
        try:
            content_length = int(request.headers["content-length"])
            if content_length > settings.max_request_size_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request payload too large"},
                )
        except ValueError:
            pass
    return await call_next(request)


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

# Add rate limiting middleware
if settings.rate_limit_enabled:
    limiter = RateLimiter(
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.add_middleware(RateLimitMiddleware, limiter=limiter)

# Include API routers
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(graph_router)

frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
