"""Organisation management: members, API keys."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import current_user, current_org, require_role
from app.core.security import generate_api_key
from app.models import User, Organisation, Membership, ApiKey
from app.models.account import MemberRole

router = APIRouter(prefix="/api/v1/orgs", tags=["orgs"])

@router.get("/{org_id}/members")
def list_members(org_id: int, _=Depends(require_role(*MemberRole)), db: Session = Depends(get_db)):
    rows = db.execute(select(Membership, User).join(User, Membership.user_id == User.id)
                      .where(Membership.org_id == org_id)).all()
    return [{"user_id": u.id, "email": u.email, "name": u.name, "role": m.role.value}
            for m, u in rows]

@router.post("/{org_id}/members")
def add_member(org_id: int, body: dict,
               _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
               db: Session = Depends(get_db)):
    """Add an existing user to the org by email. (Invitations flow comes later.)"""
    user = db.execute(select(User).where(User.email == body["email"])).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "No user with that email")
    if db.get(Membership, (user.id, org_id)):
        raise HTTPException(409, "Already a member")
    role = MemberRole(body.get("role", "member"))
    db.add(Membership(user_id=user.id, org_id=org_id, role=role)); db.commit()
    return {"user_id": user.id, "role": role.value}

@router.delete("/{org_id}/members/{user_id}")
def remove_member(org_id: int, user_id: int,
                  _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
                  db: Session = Depends(get_db)):
    m = db.get(Membership, (user_id, org_id))
    if not m:
        raise HTTPException(404, "Not a member")
    if m.role == MemberRole.owner:
        raise HTTPException(400, "Cannot remove the owner")
    db.delete(m); db.commit()
    return {"ok": True}

@router.get("/{org_id}/api-keys")
def list_keys(org_id: int, _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
              db: Session = Depends(get_db)):
    keys = db.execute(select(ApiKey).where(ApiKey.org_id == org_id)).scalars().all()
    return [{"id": k.id, "prefix": k.prefix, "label": k.label,
             "last_used": k.last_used.isoformat() if k.last_used else None} for k in keys]

@router.post("/{org_id}/api-keys")
def create_key(org_id: int, body: dict,
               _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
               db: Session = Depends(get_db)):
    raw, prefix, key_hash = generate_api_key()
    db.add(ApiKey(org_id=org_id, key_hash=key_hash, prefix=prefix, label=body.get("label")))
    db.commit()
    # plaintext shown once, never stored
    return {"api_key": raw, "prefix": prefix, "note": "Save this now — it won't be shown again."}

@router.delete("/{org_id}/api-keys/{key_id}")
def revoke_key(org_id: int, key_id: int,
               _=Depends(require_role(MemberRole.owner, MemberRole.admin)),
               db: Session = Depends(get_db)):
    k = db.get(ApiKey, key_id)
    if not k or k.org_id != org_id:
        raise HTTPException(404, "Key not found")
    db.delete(k); db.commit()
    return {"ok": True}
