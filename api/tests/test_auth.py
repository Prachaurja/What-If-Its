from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _register(email, pw="secret123"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": pw, "name": "T"})

def test_register_and_me():
    r = _register("alice@example.com")
    assert r.status_code == 200
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "alice@example.com"
    assert len(body["orgs"]) == 1 and body["orgs"][0]["role"] == "owner"

def test_login_wrong_password():
    _register("bob@example.com")
    r = client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "wrong"})
    assert r.status_code == 401

def test_duplicate_email_rejected():
    _register("carol@example.com")
    assert _register("carol@example.com").status_code == 409

def test_unauthenticated_check_rejected():
    assert client.post("/api/v1/checks/text", json={"title": "x", "text": "word " * 30}).status_code == 401
