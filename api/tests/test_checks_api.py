"""Phase 2: check endpoints require auth and run through the queue (eager in tests)."""
from app.workers.celery_app import celery
celery.conf.task_always_eager = True

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _auth(email="checker@example.com"):
    tok = client.post("/api/v1/auth/register",
                      json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}

def test_health():
    assert client.get("/api/health").json()["status"] == "ok"

def test_text_check_queues_and_completes():
    h = _auth()
    r = client.post("/api/v1/checks/text", headers=h, json={
        "title": "essay",
        "text": "Photosynthesis converts light energy into chemical energy stored in glucose molecules inside the chloroplasts of green plants, algae, and some bacteria every single day across the planet."})
    assert r.status_code == 202
    cid = r.json()["id"]
    assert client.get(f"/api/v1/checks/{cid}", headers=h).json()["status"] == "done"

def test_too_short_rejected():
    h = _auth("short@example.com")
    r = client.post("/api/v1/checks/text", headers=h, json={"title": "x", "text": "too short"})
    assert r.status_code == 400
