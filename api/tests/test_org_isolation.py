"""The security-critical test: one org cannot see another org's checks."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _user(email):
    tok = client.post("/api/v1/auth/register",
                      json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}

def test_checks_are_org_isolated():
    alice = _user("alice2@example.com")
    bob = _user("bob2@example.com")
    # alice creates a check
    r = client.post("/api/v1/checks/text", headers=alice,
                    json={"title": "essay", "text": "photosynthesis " * 40})
    assert r.status_code == 202
    cid = r.json()["id"]
    # alice can see it
    assert client.get(f"/api/v1/checks/{cid}", headers=alice).status_code == 200
    # bob cannot
    assert client.get(f"/api/v1/checks/{cid}", headers=bob).status_code == 404
    # bob's list is empty; alice's is not
    assert client.get("/api/v1/checks", headers=bob).json() == []
    assert len(client.get("/api/v1/checks", headers=alice).json()) == 1
