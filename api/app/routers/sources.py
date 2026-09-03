"""Add reference documents to the repository."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.extract import extract_text, UnsupportedFile
from app.services.similarity.index import add_document
from app.models.document import DocKind
from app.core.deps import current_user, current_org, require_role
from app.models.account import MemberRole

router = APIRouter(prefix="/api/v1", tags=["sources"])

@router.post("/sources")
async def add_source(file: UploadFile = File(...),
                     user=Depends(current_user), org_id: int = Depends(current_org),
                     _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
                     db: Session = Depends(get_db)):
    try:
        text = extract_text(file.filename, await file.read())
    except UnsupportedFile as e:
        raise HTTPException(415, str(e))
    doc = add_document(db, file.filename, text, DocKind.source, org_id=org_id)
    return {"id": doc.id, "title": doc.title, "word_count": doc.word_count}
