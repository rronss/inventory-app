from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ADMIN = "admin"
STAFF = "staff"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    # How other people see this account. The email is only for signing in and is never sent back.
    username: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(80), default="")
    role: Mapped[str] = mapped_column(String(20), default=STAFF)


# Kept as typed, but "Ron" and "ron" are the same person.
Index("ix_users_username_lower", func.lower(User.username), unique=True)


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (CheckConstraint("quantity >= 0", name="quantity_not_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[int] = mapped_column(default=0)
    reorder_level: Mapped[int] = mapped_column(default=0)
    description: Mapped[str] = mapped_column(String(1000), default="")
    # Private parts are shown to admins only. The two are chosen separately.
    stock_private: Mapped[bool] = mapped_column(default=False)  # quantity, reorder level, status
    history_private: Mapped[bool] = mapped_column(default=False)  # the movements
    images: Mapped[list["ItemImage"]] = relationship(
        lazy="selectin", order_by="ItemImage.id", cascade="all, delete-orphan"
    )

    @property
    def low_stock(self) -> bool:
        return self.quantity <= self.reorder_level

    @property
    def image_ids(self) -> list[int]:
        return [image.id for image in self.images]


class ItemImage(Base):
    """A picture of an item. The bytes are read only when the picture itself is asked for."""

    __tablename__ = "item_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    content_type: Mapped[str] = mapped_column(String(20))
    data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    change: Mapped[int]
    note: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(lazy="joined")
    item: Mapped[Item] = relationship()

    @property
    def username(self) -> str:
        return self.user.username

    @property
    def item_name(self) -> str:
        return self.item.name
