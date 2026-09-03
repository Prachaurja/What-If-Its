"""Verify the async check flow with Celery in eager mode (runs inline, no Redis)."""
from app.workers.celery_app import celery
celery.conf.task_always_eager = True   # tasks execute synchronously in-process

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _user(email):
    tok = client.post("/api/v1/auth/register",
                      json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}

def test_check_runs_and_completes():
    h = _user("dave@example.com")
    # seed a source so there's something to match
    client.post("/api/v1/sources", headers=h,
                files={"file": ("src.txt", b"Photosynthesis converts light into chemical energy stored in glucose inside chloroplasts of green plants and algae across the planet every day of the year.", "text/plain")})
    r = client.post("/api/v1/checks/text", headers=h, json={
        "title": "essay",
        "text": "In my essay: photosynthesis converts light into chemical energy stored in glucose inside chloroplasts of green plants and algae across the planet every day of the year, which is vital."})
    assert r.status_code == 202
    cid = r.json()["id"]
    # eager mode => already done by the time we poll
    got = client.get(f"/api/v1/checks/{cid}", headers=h).json()
    assert got["status"] == "done"
    assert got["payload"]["similarity_percent"] > 0
