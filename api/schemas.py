from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class WorkspaceCreate(BaseModel):
    name: str
    path: str
    language: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    path: str
    language: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    workspace_id: UUID


class SessionUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    ended_at: Optional[datetime] = None
    raw_events: Optional[dict] = None


class SessionResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    summary: Optional[str]
    model_config = {"from_attributes": True}


class MemoryCreate(BaseModel):
    type: str
    workspace_id: UUID
    session_id: Optional[UUID] = None
    title: str
    content: str
    tags: list[str] = []
    metadata: dict = {}
    source_files: list[dict] = []
    importance_score: float = 0.5


class MemoryResponse(BaseModel):
    id: UUID
    type: str
    workspace_id: UUID
    session_id: Optional[UUID]
    title: str
    content: str
    tags: list[str]
    importance_score: float
    staleness_status: str
    last_indexed_at: Optional[datetime]
    last_validated_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    workspace_id: Optional[UUID] = None
    limit: int = 5
    type_filter: Optional[str] = None


class SearchResult(BaseModel):
    memory: MemoryResponse
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


class ContextResponse(BaseModel):
    workspace_id: UUID
    memories: list[MemoryResponse]
    stale_memories: list[MemoryResponse]
    stale_files: list[dict]


class ReindexRequest(BaseModel):
    workspace_id: UUID
    file_path: str
    content: str
    language: Optional[str] = None


class StatusResponse(BaseModel):
    workspace_id: UUID
    total: int
    fresh: int
    potentially_stale: int
    confirmed_stale: int
    memories: list[MemoryResponse]
