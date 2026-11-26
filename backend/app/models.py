from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
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
    # The user this item is attached to, if any.
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)
    owner: Mapped[User | None] = relationship(lazy="joined")

    @property
    def low_stock(self) -> bool:
        return self.quantity <= self.reorder_level


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    change: Mapped[int]
    note: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship(lazy="joined")

    @property
    def username(self) -> str:
        return self.user.username
