"""Check endpoints. Phase 0: synchronous. Same shapes the async version will use."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.check import TextCheck
from app.services.extract import extract_text, UnsupportedFile
from app.services.report import run_check, TooShort
from app.models import Check
from app.models.check import CheckStatus

router = APIRouter(prefix="/api/v1", tags=["checks"])

def _persist(db: Session, report: dict) -> dict:
    ai = report.get("ai") or {}
    check = Check(document_id=report["document_id"], status=CheckStatus.done,
                  similarity_pct=report["similarity_percent"],
                  ai_prob=ai.get("prob"), payload=report)
    db.add(check); db.commit()
    report["check_id"] = check.id
    return report

@router.post("/checks")
async def create_check(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        text = extract_text(file.filename, await file.read())
        return _persist(db, run_check(db, file.filename, text))
    except UnsupportedFile as e:
        raise HTTPException(415, str(e))
    except TooShort as e:
        raise HTTPException(400, str(e))

@router.post("/checks/text")
def create_check_text(body: TextCheck, db: Session = Depends(get_db)):
    try:
        return _persist(db, run_check(db, body.title, body.text))
    except TooShort as e:
        raise HTTPException(400, str(e))

@router.get("/checks/{check_id}")
def get_check(check_id: int, db: Session = Depends(get_db)):
    check = db.get(Check, check_id)
    if not check:
        raise HTTPException(404, "Check not found")
    return {"id": check.id, "status": check.status.value,
            "similarity_pct": check.similarity_pct, "payload": check.payload}
