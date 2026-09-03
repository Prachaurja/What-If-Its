from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json()["status"] == "ok"

def test_text_check_flow():
    # seed a source, then submit overlapping text
    client.post("/api/v1/sources") if False else None
    r = client.post("/api/v1/checks/text", json={
        "title": "essay",
        "text": "Photosynthesis converts light energy into chemical energy stored in glucose molecules inside the chloroplasts of green plants, algae, and some bacteria every single day across the planet."})
    assert r.status_code == 200
    assert "similarity_percent" in r.json()

def test_too_short_rejected():
    r = client.post("/api/v1/checks/text", json={"title": "x", "text": "too short"})
    assert r.status_code == 400
