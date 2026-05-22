import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import mapped_column, Mapped, relationship
from pgvector.sqlalchemy import Vector
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sessions: Mapped[list["Session"]] = relationship(back_populates="workspace")
    memories: Mapped[list["Memory"]] = relationship(back_populates="workspace")
    file_index: Mapped[list["FileIndex"]] = relationship(back_populates="workspace")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_events: Mapped[dict] = mapped_column(JSON, default=dict)

    workspace: Mapped["Workspace"] = relationship(back_populates="sessions")
    memories: Mapped[list["Memory"]] = relationship(back_populates="session")


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String, nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    source_files: Mapped[list] = mapped_column(JSON, default=list)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    staleness_status: Mapped[str] = mapped_column(String, default="fresh")
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_level: Mapped[str] = mapped_column(String, default="private")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    workspace: Mapped["Workspace"] = relationship(back_populates="memories")
    session: Mapped["Session | None"] = relationship(back_populates="memories")


class FileIndex(Base):
    __tablename__ = "file_index"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    memory_ids: Mapped[list] = mapped_column(JSON, default=list)

    workspace: Mapped["Workspace"] = relationship(back_populates="file_index")
