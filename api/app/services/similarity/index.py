"""Add documents to the fingerprint index and find candidate sources for a
submission. The index is the `fingerprints` table; candidate lookup is one
GROUP BY query.
"""
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Document, Fingerprint
from app.models.document import DocKind
from app.services.similarity.shingle import shingles
from app.services.similarity.winnow import fingerprints, h
from app.core.config import settings

def text_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).lower().encode()).hexdigest()

def add_document(db: Session, title: str, text: str, kind: DocKind, org_id: int | None = None) -> Document:
    doc = Document(org_id=org_id, kind=kind, title=title, text=text,
                   text_hash=text_hash(text), word_count=len(text.split()))
    db.add(doc); db.flush()
    fps = fingerprints(shingles(text))
    db.add_all(Fingerprint(hash=hv, doc_id=doc.id, pos=pos) for hv, pos in fps)
    doc.indexed_at = datetime.now(timezone.utc)
    db.commit()
    return doc

def candidates(db: Session, text: str, org_id: int | None = None,
               exclude_id: int | None = None) -> dict[int, tuple[str, set]]:
    """Return {doc_id: (title, shingle_set)} for documents sharing enough
    fingerprints. Scoped to the org's docs plus shared (org_id NULL) content.
    """
    fps = [hv for hv, _ in fingerprints(shingles(text))]
    if not fps:
        return {}
    q = (select(Fingerprint.doc_id, func.count().label("n"))
         .where(Fingerprint.hash.in_(fps))
         .group_by(Fingerprint.doc_id)
         .having(func.count() >= settings.min_shared))
    ids = [r.doc_id for r in db.execute(q)]
    if not ids:
        return {}
    docs_q = select(Document).where(Document.id.in_(ids))
    # org scoping: this org's docs OR shared docs (org_id IS NULL)
    if org_id is not None:
        docs_q = docs_q.where((Document.org_id == org_id) | (Document.org_id.is_(None)))
    out = {}
    for d in db.execute(docs_q).scalars():
        if d.id != exclude_id:
            out[d.id] = (d.title, set(shingles(d.text)))
    return out
