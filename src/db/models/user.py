"""User-domain SQLAlchemy models mirrored from the backend schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import UserProvider, UserRole

if TYPE_CHECKING:
    from src.db.models.lesson import Booking, Lesson, LessonReview
    from src.db.models.product import ProductBookmark, ProductReview


class User(Base):
    """Read-only mirror of the ``users`` table."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    provider: Mapped[UserProvider] = mapped_column(SqlEnum(UserProvider), nullable=False)
    provider_id: Mapped[str] = mapped_column("providerId", String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    careers: Mapped[list[Career]] = relationship(back_populates="user")
    product_bookmarks: Mapped[list[ProductBookmark]] = relationship(back_populates="user")
    product_reviews: Mapped[list[ProductReview]] = relationship(back_populates="user")
    lessons: Mapped[list[Lesson]] = relationship(back_populates="host_user")
    bookings: Mapped[list[Booking]] = relationship(back_populates="user")
    lesson_reviews: Mapped[list[LessonReview]] = relationship(back_populates="user")


class Career(Base):
    """Read-only mirror of instructor/host career entries."""

    __tablename__ = "career"

    career_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship(back_populates="careers")
