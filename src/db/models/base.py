"""SQLAlchemy declarative base for read-only backend schema mirrors."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for AI-side SQLAlchemy models.

    These models mirror the backend-owned MySQL schema for read operations only.
    Do not call ``Base.metadata.create_all()`` from the AI server.
    """

