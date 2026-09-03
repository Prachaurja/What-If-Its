from pydantic import BaseModel, EmailStr
from app.models.account import OrgType

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    org_type: OrgType = OrgType.individual
    org_name: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OrgOut(BaseModel):
    id: int
    name: str
    type: OrgType
    plan: str
    role: str

class MeOut(BaseModel):
    id: int
    email: str
    name: str | None
    orgs: list[OrgOut]
