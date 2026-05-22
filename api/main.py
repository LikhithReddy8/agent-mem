from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import workspaces, sessions, memories, search
from .embeddings import get_embedder


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_embedder()  # warm up model at startup so first request isn't slow
    yield


app = FastAPI(title="agent-mem", version="0.1.0", lifespan=lifespan)
app.include_router(workspaces.router)
app.include_router(sessions.router)
app.include_router(memories.router)
app.include_router(search.router)
