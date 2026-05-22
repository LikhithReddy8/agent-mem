import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models import Memory, FileIndex
from ..schemas import (
    SearchRequest, SearchResponse, SearchResult,
    ContextResponse, ReindexRequest, StatusResponse, MemoryResponse
)
from ..embeddings import embed_text
from ..staleness import compute_staleness_status, hash_file

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search_memories(body: SearchRequest, db: AsyncSession = Depends(get_db)):
    query_embedding = embed_text(body.query)
    stmt = (
        select(
            Memory,
            Memory.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .order_by("distance")
        .limit(body.limit)
    )
    if body.workspace_id:
        stmt = stmt.where(Memory.workspace_id == body.workspace_id)
    if body.type_filter:
        stmt = stmt.where(Memory.type == body.type_filter)
    result = await db.execute(stmt)
    rows = result.all()
    return SearchResponse(results=[
        SearchResult(memory=MemoryResponse.model_validate(row.Memory), score=1 - row.distance)
        for row in rows
        if row.Memory.embedding is not None
    ])


@router.get("/context/{workspace_id}", response_model=ContextResponse)
async def get_context(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Memory)
        .where(Memory.workspace_id == workspace_id)
        .order_by(Memory.importance_score.desc(), Memory.created_at.desc())
        .limit(10)
    )
    memories = result.scalars().all()

    stale_result = await db.execute(
        select(Memory)
        .where(
            Memory.workspace_id == workspace_id,
            Memory.staleness_status.in_(["potentially_stale", "confirmed_stale"]),
        )
    )
    stale_memories = stale_result.scalars().all()

    fi_result = await db.execute(
        select(FileIndex).where(FileIndex.workspace_id == workspace_id)
    )
    file_entries = fi_result.scalars().all()
    stale_files = []
    now = datetime.now(timezone.utc)
    for fi in file_entries:
        try:
            current_hash = hash_file(fi.file_path)
        except (FileNotFoundError, PermissionError):
            continue
        days = (now - fi.last_indexed_at).total_seconds() / 86400
        status = compute_staleness_status(current_hash, fi.file_hash, days)
        if status != "fresh":
            stale_files.append({"path": fi.file_path, "status": status, "days_since_indexed": days})

    return ContextResponse(
        workspace_id=workspace_id,
        memories=[MemoryResponse.model_validate(m) for m in memories],
        stale_memories=[MemoryResponse.model_validate(m) for m in stale_memories],
        stale_files=stale_files,
    )


@router.post("/reindex")
async def reindex_file(body: ReindexRequest, db: AsyncSession = Depends(get_db)):
    import hashlib
    content_hash = hashlib.sha256(body.content.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(FileIndex).where(
            FileIndex.workspace_id == body.workspace_id,
            FileIndex.file_path == body.file_path,
        )
    )
    fi = result.scalar_one_or_none()
    if fi:
        fi.file_hash = content_hash
        fi.last_indexed_at = now
        fi.last_checked_at = now
    else:
        fi = FileIndex(
            workspace_id=body.workspace_id,
            file_path=body.file_path,
            file_hash=content_hash,
            language=body.language,
            last_indexed_at=now,
        )
        db.add(fi)
    await db.commit()
    return {"status": "reindexed", "file_path": body.file_path, "hash": content_hash}


@router.get("/status/{workspace_id}", response_model=StatusResponse)
async def get_status(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Memory).where(Memory.workspace_id == workspace_id)
    )
    all_memories = result.scalars().all()
    by_status = {"fresh": 0, "potentially_stale": 0, "confirmed_stale": 0}
    for m in all_memories:
        key = m.staleness_status if m.staleness_status in by_status else "fresh"
        by_status[key] += 1
    return StatusResponse(
        workspace_id=workspace_id,
        total=len(all_memories),
        fresh=by_status["fresh"],
        potentially_stale=by_status["potentially_stale"],
        confirmed_stale=by_status["confirmed_stale"],
        memories=[MemoryResponse.model_validate(m) for m in all_memories],
    )
