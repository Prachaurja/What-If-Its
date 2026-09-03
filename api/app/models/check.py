"""A Check is one run against a submission; CheckSource is one matched source.
The full render payload lives in Check.payload (JSON)."""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.base import Base
from app.models.document import Document  # noqa: E402,F401

class CheckStatus(str, enum.Enum):
    queued = "queued"; running = "running"; done = "done"; failed = "failed"

class Check(Base):
    __tablename__ = "checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[CheckStatus] = mapped_column(Enum(CheckStatus), default=CheckStatus.queued)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    similarity_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_prob: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    document: Mapped["Document"] = relationship("Document")
    sources: Mapped[list["CheckSource"]] = relationship(back_populates="check", cascade="all, delete-orphan")

class CheckSource(Base):
    __tablename__ = "check_sources"
    check_id: Mapped[int] = mapped_column(ForeignKey("checks.id", ondelete="CASCADE"), primary_key=True)
    source_doc_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), primary_key=True)
    percent: Mapped[float] = mapped_column(Float)
    passages: Mapped[list] = mapped_column(JSON, default=list)
    check: Mapped["Check"] = relationship(back_populates="sources")
