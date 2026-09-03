"""Check endpoints — now asynchronous and org-scoped.

POST creates a Check row (status=queued) and hands the work to Celery, returning
immediately. GET polls for status/result. Everything is scoped to the caller's
active organisation.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.check import TextCheck
from app.services.extract import extract_text, UnsupportedFile
from app.services.similarity.index import add_document, text_hash
from app.services.report import MIN_WORDS
from app.models import Check, Document
from app.models.check import CheckStatus
from app.models.document import DocKind
from app.core.deps import current_user, current_org, require_role
from app.models.account import MemberRole

router = APIRouter(prefix="/api/v1", tags=["checks"])

def _enqueue(db: Session, title: str, text: str, org_id: int, user_id: int,
             options: dict) -> Check:
    if len(text.split()) < MIN_WORDS if False else len(text.split()) < 20:
        raise HTTPException(400, "Document is too short to check (need at least 20 words)")
    doc = add_document(db, title, text, DocKind.submission, org_id=org_id)
    check = Check(org_id=org_id, document_id=doc.id, created_by=user_id,
                  status=CheckStatus.queued, options=options)
    db.add(check); db.commit()
    # enqueue; if the broker is down we still return the row (status stays queued)
    try:
        from app.workers.tasks import run_check
        run_check.delay(check.id)
    except Exception:
        pass
    return check

DEFAULT_OPTIONS = {"run_ai": True, "web_fallback": False,
                   "exclude_quotes": False, "exclude_references": True}

@router.post("/checks", status_code=202)
async def create_check(file: UploadFile = File(...),
                       user=Depends(current_user), org_id: int = Depends(current_org),
                       _=Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
                       db: Session = Depends(get_db)):
    try:
        text = extract_text(file.filename, await file.read())
    except UnsupportedFile as e:
        raise HTTPException(415, str(e))
    check = _enqueue(db, file.filename, text, org_id, user.id, dict(DEFAULT_OPTIONS))
    return {"id": check.id, "status": check.status.value}

@router.post("/checks/text", status_code=202)
def create_check_text(body: TextCheck,
                      user=Depends(current_user), org_id: int = Depends(current_org),
                      _=Depends(require_role(MemberRole.owner, MemberRole.admin, MemberRole.member)),
                      db: Session = Depends(get_db)):
    check = _enqueue(db, body.title, body.text, org_id, user.id, dict(DEFAULT_OPTIONS))
    return {"id": check.id, "status": check.status.value}

@router.get("/checks")
def list_checks(user=Depends(current_user), org_id: int = Depends(current_org),
                db: Session = Depends(get_db), limit: int = 50):
    rows = db.execute(select(Check).where(Check.org_id == org_id)
                      .order_by(Check.created_at.desc()).limit(limit)).scalars().all()
    return [{"id": c.id, "status": c.status.value, "similarity_pct": c.similarity_pct,
             "ai_prob": c.ai_prob, "created_at": c.created_at.isoformat()} for c in rows]

@router.get("/checks/{check_id}")
def get_check(check_id: int, user=Depends(current_user),
              org_id: int = Depends(current_org), db: Session = Depends(get_db)):
    check = db.get(Check, check_id)
    if not check or check.org_id != org_id:
        raise HTTPException(404, "Check not found")
    return {"id": check.id, "status": check.status.value,
            "similarity_pct": check.similarity_pct, "ai_prob": check.ai_prob,
            "error": check.error, "payload": check.payload if check.status == CheckStatus.done else None}
