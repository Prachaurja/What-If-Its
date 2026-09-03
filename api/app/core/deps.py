"""FastAPI dependencies for auth and org-scoping. This is the security gate every
protected route uses: resolve the user, resolve the active org, enforce roles.
"""
from __future__ import annotations
from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token, hash_api_key
from app.models import User, Membership, ApiKey
from app.models.account import MemberRole

def current_user(request: Request,
                 authorization: str | None = Header(default=None),
                 x_api_key: str | None = Header(default=None),
                 db: Session = Depends(get_db)) -> User:
    """Resolve the user from a Bearer JWT or an X-API-Key header."""
    # API key path
    if x_api_key:
        key = db.execute(select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key))).scalar_one_or_none()
        if not key:
            raise HTTPException(401, "Invalid API key")
        # API keys act as the org owner
        m = db.execute(select(Membership).where(Membership.org_id == key.org_id,
                       Membership.role == MemberRole.owner)).scalar_one_or_none()
        request.state.org_id = key.org_id
        if m:
            return db.get(User, m.user_id)
        raise HTTPException(401, "API key org has no owner")

    # JWT path
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    request.state.org_id = payload.get("org")
    return user

def current_org(request: Request,
                x_org_id: int | None = Header(default=None),
                user: User = Depends(current_user),
                db: Session = Depends(get_db)) -> int:
    """Resolve the active org id: explicit X-Org-Id header, else the token's org,
    else the user's first membership. Always verifies the user belongs to it."""
    org_id = x_org_id or getattr(request.state, "org_id", None)
    memberships = db.execute(select(Membership).where(Membership.user_id == user.id)).scalars().all()
    if not memberships:
        raise HTTPException(403, "User has no organisation")
    valid_ids = {m.org_id for m in memberships}
    if org_id is None:
        org_id = memberships[0].org_id
    if org_id not in valid_ids:
        raise HTTPException(403, "Not a member of this organisation")
    return org_id

def require_role(*roles: MemberRole):
    """Dependency factory: require the user to hold one of `roles` in the active org."""
    def dep(user: User = Depends(current_user),
            org_id: int = Depends(current_org),
            db: Session = Depends(get_db)) -> Membership:
        m = db.get(Membership, (user.id, org_id))
        if not m or m.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return m
    return dep
