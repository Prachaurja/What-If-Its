"""Authentication: register, login, refresh, logout, me."""
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import (hash_password, verify_password, create_access_token,
                               create_refresh_token, decode_token)
from app.core.deps import current_user
from app.models import User, Organisation, Membership
from app.models.account import MemberRole, OrgType
from app.schemas.auth import RegisterIn, LoginIn, TokenOut, MeOut, OrgOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def _set_refresh_cookie(resp: Response, user_id: int):
    resp.set_cookie("refresh_token", create_refresh_token(user_id),
                    httponly=True, samesite="lax", max_age=60*60*24*30, path="/api/v1/auth")

@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, resp: Response, db: Session = Depends(get_db)):
    if db.execute(select(User).where(User.email == body.email)).scalar_one_or_none():
        raise HTTPException(409, "Email already registered")
    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    db.add(user); db.flush()
    org = Organisation(name=body.org_name or (body.name or body.email.split("@")[0]) + "'s workspace",
                       type=body.org_type)
    db.add(org); db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role=MemberRole.owner))
    db.commit()
    _set_refresh_cookie(resp, user.id)
    return TokenOut(access_token=create_access_token(user.id, org.id))

@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, resp: Response, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    first_org = db.execute(select(Membership).where(Membership.user_id == user.id)).scalar_one_or_none()
    _set_refresh_cookie(resp, user.id)
    return TokenOut(access_token=create_access_token(user.id, first_org.org_id if first_org else None))

@router.post("/refresh", response_model=TokenOut)
def refresh(db: Session = Depends(get_db), refresh_token: str | None = Cookie(default=None)):
    payload = decode_token(refresh_token) if refresh_token else None
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    user_id = int(payload["sub"])
    first_org = db.execute(select(Membership).where(Membership.user_id == user_id)).scalar_one_or_none()
    return TokenOut(access_token=create_access_token(user_id, first_org.org_id if first_org else None))

@router.post("/logout")
def logout(resp: Response):
    resp.delete_cookie("refresh_token", path="/api/v1/auth")
    return {"ok": True}

@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Membership, Organisation)
                      .join(Organisation, Membership.org_id == Organisation.id)
                      .where(Membership.user_id == user.id)).all()
    orgs = [OrgOut(id=o.id, name=o.name, type=o.type, plan=o.plan, role=m.role.value)
            for m, o in rows]
    return MeOut(id=user.id, email=user.email, name=user.name, orgs=orgs)
