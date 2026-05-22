from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import workspaces, sessions, memories


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="agent-mem", lifespan=lifespan)
app.include_router(workspaces.router)
app.include_router(sessions.router)
app.include_router(memories.router)
