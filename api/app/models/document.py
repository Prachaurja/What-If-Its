"""Documents (sources, submissions, cached web pages) and the fingerprint index.

Every piece of text Swipe knows about is a Document. Fingerprints are the
inverted index: one row per (hash, document). org_id is NULL for shared
content (public corpus, web cache) and set for a specific org's private docs.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, Text, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.base import Base

class DocKind(str, enum.Enum):
    submission = "submission"; source = "source"; web = "web"

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True)
    kind: Mapped[DocKind] = mapped_column(Enum(DocKind))
    title: Mapped[str] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64))
    word_count: Mapped[int] = mapped_column(Integer)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    fingerprints: Mapped[list["Fingerprint"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    __table_args__ = (Index("ix_documents_org_kind", "org_id", "kind"), Index("ix_documents_text_hash", "text_hash"))

class Fingerprint(Base):
    __tablename__ = "fingerprints"
    # Composite PK (no surrogate id) keeps this huge table as small as possible.
    hash: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    pos: Mapped[int] = mapped_column(Integer, primary_key=True)
    document: Mapped["Document"] = relationship(back_populates="fingerprints")
    __table_args__ = (Index("ix_fingerprints_hash", "hash"),)
