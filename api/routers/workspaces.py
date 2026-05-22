from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from ..db import get_db
from ..models import Workspace
from ..schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(body: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    ws = Workspace(name=body.name, path=body.path, language=body.language)
    db.add(ws)
    try:
        await db.commit()
        await db.refresh(ws)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Workspace with this path already exists")
    return ws


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return result.scalars().all()
