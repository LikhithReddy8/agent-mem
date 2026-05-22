import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Memory
from ..schemas import MemoryCreate, MemoryResponse
from ..embeddings import embed_text

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=MemoryResponse, status_code=201)
async def create_memory(body: MemoryCreate, db: AsyncSession = Depends(get_db)):
    embedding = embed_text(f"{body.title} {body.content}")
    now = datetime.now(timezone.utc)
    memory = Memory(
        type=body.type,
        workspace_id=body.workspace_id,
        session_id=body.session_id,
        title=body.title,
        content=body.content,
        embedding=embedding,
        tags=body.tags,
        metadata_=body.metadata,
        source_files=body.source_files,
        importance_score=body.importance_score,
        last_indexed_at=now,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    await db.delete(memory)
    await db.commit()


@router.patch("/{memory_id}/validate", response_model=MemoryResponse)
async def validate_memory(memory_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.staleness_status = "fresh"
    memory.last_validated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(memory)
    return memory


class FlagStaleBody(BaseModel):
    reason: str = ""


@router.patch("/{memory_id}/flag-stale", response_model=MemoryResponse)
async def flag_stale_memory(memory_id: uuid.UUID, body: FlagStaleBody, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    memory.staleness_status = "confirmed_stale"
    await db.commit()
    await db.refresh(memory)
    return memory
