"""Runs a full check: index the submission, find candidates, build the report.
In Phase 0 this runs inline in the request. Phase 2 moves it into a Celery task
unchanged — it already takes a plain session and returns a dict.
"""
from sqlalchemy.orm import Session
from app.models.document import DocKind
from app.services.similarity.index import add_document, candidates
from app.services.similarity.match import build_report

MIN_WORDS = 20

class TooShort(Exception):
    pass

def run_check(db: Session, title: str, text: str, org_id: int | None = None,
              run_ai: bool = True) -> dict:
    if len(text.split()) < MIN_WORDS:
        raise TooShort(f"Need at least {MIN_WORDS} words to check")
    doc = add_document(db, title, text, DocKind.submission, org_id=org_id)
    sources = candidates(db, text, org_id=org_id, exclude_id=doc.id)
    report = build_report(text, sources)
    report["document_id"] = doc.id
    report["title"] = title
    report["text"] = text
    # AI detection (Phase 1). Runs Binoculars if torch + models are installed;
    # otherwise degrades to "not scored" without breaking the similarity check.
    if run_ai:
        try:
            from app.services.ai_detect.ensemble import run as run_ai_detect
            report["ai"] = run_ai_detect(text)
        except Exception as e:
            report["ai"] = {"scored": False, "reason": f"AI detector unavailable: {e}",
                            "prob": None, "band": None, "verdict": "not scored"}
    else:
        report["ai"] = None
    return report
