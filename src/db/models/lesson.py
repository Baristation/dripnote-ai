"""Lesson-domain SQLAlchemy models mirrored from the backend schema."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import (
    BookingStatus,
    DifficultyLevel,
    ImageType,
    LessonCategory,
    Region,
    ScheduleStatus,
)

if TYPE_CHECKING:
    from src.db.models.user import User


class Lesson(Base):
    """Read-only mirror of barista lessons/classes."""

    __tablename__ = "lessons"

    lesson_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(255))
    lesson_category: Mapped[LessonCategory | None] = mapped_column(SqlEnum(LessonCategory))
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SqlEnum(DifficultyLevel), nullable=False
    )
    region: Mapped[Region | None] = mapped_column(SqlEnum(Region))
    city: Mapped[str | None] = mapped_column(String(50))
    place: Mapped[str | None] = mapped_column(String(150))
    address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    host_user: Mapped[User] = relationship(back_populates="lessons")
    curriculum_items: Mapped[list[LessonCurriculum]] = relationship(back_populates="lesson")
    images: Mapped[list[LessonImage]] = relationship(back_populates="lesson")
    schedules: Mapped[list[LessonSchedule]] = relationship(back_populates="lesson")
    reviews: Mapped[list[LessonReview]] = relationship(back_populates="lesson")


class LessonCurriculum(Base):
    """Read-only mirror of ordered lesson curriculum items."""

    __tablename__ = "lesson_curriculum"

    lesson_curriculum_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="curriculum_items")


class LessonImage(Base):
    """Read-only mirror of lesson image data."""

    __tablename__ = "lesson_images"

    lesson_image_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_type: Mapped[ImageType | None] = mapped_column(SqlEnum(ImageType))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="images")


class LessonSchedule(Base):
    """Read-only mirror of lesson schedules."""

    __tablename__ = "lesson_schedules"
    __table_args__ = (UniqueConstraint("lesson_id", "lesson_date", "start_time"),)

    lesson_schedule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), nullable=False)
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_count: Mapped[int] = mapped_column(Integer, nullable=False)
    schedule_status: Mapped[ScheduleStatus] = mapped_column(SqlEnum(ScheduleStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    lesson: Mapped[Lesson] = relationship(back_populates="schedules")
    bookings: Mapped[list[Booking]] = relationship(back_populates="lesson_schedule")


class Booking(Base):
    """Read-only mirror of lesson booking data."""

    __tablename__ = "bookings"

    booking_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    class_schedule_id: Mapped[int] = mapped_column(
        ForeignKey("lesson_schedules.lesson_schedule_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    booking_status: Mapped[BookingStatus] = mapped_column(SqlEnum(BookingStatus), nullable=False)
    attendee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    attendee_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    booked_price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    lesson_schedule: Mapped[LessonSchedule] = relationship(back_populates="bookings")
    user: Mapped[User] = relationship(back_populates="bookings")
    lesson_review: Mapped[LessonReview | None] = relationship(
        back_populates="booking", uselist=False
    )


class LessonReview(Base):
    """Read-only mirror of reviews written after completed lesson bookings."""

    __tablename__ = "lesson_reviews"

    lesson_review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.booking_id"), unique=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.lesson_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    booking: Mapped[Booking] = relationship(back_populates="lesson_review")
    lesson: Mapped[Lesson] = relationship(back_populates="reviews")
    user: Mapped[User] = relationship(back_populates="lesson_reviews")
