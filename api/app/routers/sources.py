"""Add reference documents to the repository."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.extract import extract_text, UnsupportedFile
from app.services.similarity.index import add_document
from app.models.document import DocKind

router = APIRouter(prefix="/api/v1", tags=["sources"])

@router.post("/sources")
async def add_source(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        text = extract_text(file.filename, await file.read())
    except UnsupportedFile as e:
        raise HTTPException(415, str(e))
    doc = add_document(db, file.filename, text, DocKind.source)
    return {"id": doc.id, "title": doc.title, "word_count": doc.word_count}
