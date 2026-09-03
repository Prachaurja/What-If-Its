"""Import every model here so `from app import models` registers them all
with SQLAlchemy's metadata (needed by Alembic autogenerate).
"""
from app.models.account import Organisation, User, Membership  # noqa: F401
from app.models.document import Document, Fingerprint          # noqa: F401
from app.models.check import Check, CheckSource                # noqa: F401
