"""Background tasks. run_check does the slow work (similarity + AI detection) off
the request path, updating the Check row as it goes so the frontend can poll.
"""
from datetime import datetime, timezone
from app.workers.celery_app import celery
from app.db.session import SessionLocal
from app.models import Check
from app.models.check import CheckStatus
from app.services.similarity.index import candidates
from app.services.similarity.match import build_report

@celery.task(bind=True, max_retries=2)
def run_check(self, check_id: int):
    db = SessionLocal()
    try:
        check = db.get(Check, check_id)
        if not check:
            return
        check.status = CheckStatus.running
        check.started_at = datetime.now(timezone.utc) if hasattr(check, "started_at") else None
        db.commit()

        doc = check.document
        text = doc.text
        sources = candidates(db, text, org_id=check.org_id, exclude_id=doc.id)
        report = build_report(text, sources)
        report["document_id"] = doc.id
        report["title"] = doc.title
        report["text"] = text

        # AI detection (uses trained model if present, else graceful fallback)
        if check.options.get("run_ai", True):
            try:
                from app.services.ai_detect.ensemble import run as run_ai_detect
                report["ai"] = run_ai_detect(text)
            except Exception as e:  # noqa: BLE001
                report["ai"] = {"scored": False, "reason": f"AI detector unavailable: {e}",
                                "prob": None, "band": None, "verdict": "not scored"}
        else:
            report["ai"] = None

        ai = report.get("ai") or {}
        check.similarity_pct = report["similarity_percent"]
        check.ai_prob = ai.get("prob")
        check.payload = report
        check.status = CheckStatus.done
        db.commit()
    except Exception as e:  # noqa: BLE001
        check = db.get(Check, check_id)
        if check:
            check.status = CheckStatus.failed
            check.error = str(e)
            db.commit()
        raise self.retry(exc=e, countdown=10)
    finally:
        db.close()
