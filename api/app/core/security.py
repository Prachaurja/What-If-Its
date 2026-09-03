"""Password hashing, JWT tokens, and API-key hashing. No FastAPI here — pure
functions so they're easy to test and reuse from the worker.
"""
from __future__ import annotations
import hashlib, secrets
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings

# bcrypt caps input at 72 bytes; we hash longer passwords through sha256 first so
# the full password still contributes (a common, safe pattern).
def _prehash(plain: str) -> bytes:
    raw = plain.encode("utf-8")
    if len(raw) > 72:
        raw = hashlib.sha256(raw).hexdigest().encode("utf-8")
    return raw

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_prehash(plain), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(plain), hashed.encode("utf-8"))
    except ValueError:
        return False

def create_access_token(user_id: int, org_id: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "org": org_id, "type": "access",
               "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": "refresh",
               "iat": now, "exp": now + timedelta(days=settings.refresh_token_days)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

# --- API keys: shown once, stored hashed ---
def generate_api_key() -> tuple[str, str, str]:
    """Return (plaintext, prefix, sha256_hash). Plaintext is shown to the user once."""
    raw = "sk_live_" + secrets.token_urlsafe(24)
    return raw, raw[:12], hashlib.sha256(raw.encode()).hexdigest()

def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
