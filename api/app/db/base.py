"""Declarative base. Every model inherits from Base so Alembic can see them."""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
