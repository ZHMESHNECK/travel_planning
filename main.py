from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.engine import Base, engine
from app.routers import projects, places


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Travel Planner API",
    description=(
        "A management application that helps travellers plan trips and collect "
        "desired places to visit. Places are artworks from the Art Institute of Chicago."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "Travel Planner API"}