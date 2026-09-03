"""Accounts: organisations, users, memberships, API keys.

Multi-tenancy lives here. A user can belong to several orgs via memberships;
every piece of data (documents, checks) is scoped by org_id. Roles gate actions.
"""
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.db.base import Base

def _now(): return datetime.now(timezone.utc)

class OrgType(str, enum.Enum):
    institution = "institution"
    publisher = "publisher"
    individual = "individual"

class MemberRole(str, enum.Enum):
    owner = "owner"; admin = "admin"; member = "member"; viewer = "viewer"

class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[OrgType] = mapped_column(Enum(OrgType), default=OrgType.individual)
    plan: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    memberships: Mapped[list["Membership"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="org", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    memberships: Mapped[list["Membership"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Membership(Base):
    __tablename__ = "memberships"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.owner)
    user: Mapped["User"] = relationship(back_populates="memberships")
    org: Mapped["Organisation"] = relationship(back_populates="memberships")

class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organisations.id", ondelete="CASCADE"))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prefix: Mapped[str] = mapped_column(String(16))
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    org: Mapped["Organisation"] = relationship(back_populates="api_keys")
