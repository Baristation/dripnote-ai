"""Product-domain SQLAlchemy models mirrored from the backend schema."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base
from src.db.models.enums import FlavorCategory, ImageType, RoastingLevel

if TYPE_CHECKING:
    from src.db.models.user import User


class Roaster(Base):
    """Read-only mirror of roastery/brand data."""

    __tablename__ = "roasters"

    roaster_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name_ko: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    homepage_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    products: Mapped[list[Product]] = relationship(back_populates="roaster")


class Bean(Base):
    """Read-only mirror of base coffee bean attributes."""

    __tablename__ = "bean"

    bean_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name_ko: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    process: Mapped[str | None] = mapped_column(String(100))
    origin: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    variety: Mapped[str | None] = mapped_column(String(100))
    altitude_min: Mapped[int | None] = mapped_column(Integer)
    altitude_max: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product_links: Mapped[list[BeanProduct]] = relationship(back_populates="bean")


class Product(Base):
    """Read-only mirror of the sellable product table."""

    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    roaster_id: Mapped[int] = mapped_column(ForeignKey("roasters.roaster_id"), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    roasting_level: Mapped[RoastingLevel | None] = mapped_column(SqlEnum(RoastingLevel))
    agtron_min: Mapped[int | None] = mapped_column(Integer)
    agtron_max: Mapped[int | None] = mapped_column(Integer)
    acidity: Mapped[int | None] = mapped_column(Integer)
    sweetness: Mapped[int | None] = mapped_column(Integer)
    body: Mapped[int | None] = mapped_column(Integer)
    balance: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    product_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    roaster: Mapped[Roaster] = relationship(back_populates="products")
    bean_links: Mapped[list[BeanProduct]] = relationship(back_populates="product")
    flavor_links: Mapped[list[ProductFlavorNote]] = relationship(back_populates="product")
    images: Mapped[list[ProductImage]] = relationship(back_populates="product")
    bookmarks: Mapped[list[ProductBookmark]] = relationship(back_populates="product")
    reviews: Mapped[list[ProductReview]] = relationship(back_populates="product")


class BeanProduct(Base):
    """Read-only mirror of the product-bean many-to-many mapping table."""

    __tablename__ = "bean_product"

    bean_product_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    bean_id: Mapped[int] = mapped_column(ForeignKey("bean.bean_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product: Mapped[Product] = relationship(back_populates="bean_links")
    bean: Mapped[Bean] = relationship(back_populates="product_links")


class FlavorNote(Base):
    """Read-only mirror of flavor note master data."""

    __tablename__ = "flavor_note"

    flavor_note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    flavor_category: Mapped[FlavorCategory | None] = mapped_column(SqlEnum(FlavorCategory))
    name_ko: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(50))
    flavor_image_url: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product_links: Mapped[list[ProductFlavorNote]] = relationship(back_populates="flavor_note")


class ProductFlavorNote(Base):
    """Read-only mirror of the product-flavor many-to-many mapping table."""

    __tablename__ = "product_flavor_note"
    __table_args__ = (
        UniqueConstraint("product_id", "flavor_note_id"),
        Index("ix_product_flavor_note_flavor_note_id", "flavor_note_id"),
    )

    product_flavor_note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False)
    flavor_note_id: Mapped[int] = mapped_column(
        ForeignKey("flavor_note.flavor_note_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product: Mapped[Product] = relationship(back_populates="flavor_links")
    flavor_note: Mapped[FlavorNote] = relationship(back_populates="product_links")


class ProductImage(Base):
    """Read-only mirror of product image data."""

    __tablename__ = "product_images"

    product_image_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_type: Mapped[ImageType | None] = mapped_column(SqlEnum(ImageType))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product: Mapped[Product] = relationship(back_populates="images")


class ProductBookmark(Base):
    """Read-only mirror of user product bookmarks."""

    __tablename__ = "product_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)

    bookmark_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship(back_populates="product_bookmarks")
    product: Mapped[Product] = relationship(back_populates="bookmarks")


class ProductReview(Base):
    """Read-only mirror of product text reviews."""

    __tablename__ = "product_reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)

    product_review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped[User] = relationship(back_populates="product_reviews")
    product: Mapped[Product] = relationship(back_populates="reviews")
