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
    bio: Mapped[str] = mapped_column(String(500), default="")
    # What a staff account may do. Admins may always do all of it.
    can_add_items: Mapped[bool] = mapped_column(default=True)
    can_move_stock: Mapped[bool] = mapped_column(default=True)
    can_edit_items: Mapped[bool] = mapped_column(default=True)
    # Stock and edits only for items they added. Set for people who register themselves.
    own_items_only: Mapped[bool] = mapped_column(default=False)
    chat_from: Mapped[str] = mapped_column(String(10), default="everyone")  # or "friends"
    # Counts uploads, so the page knows when to fetch the photo again. 0 means there is none.
    photo_version: Mapped[int] = mapped_column(default=0)


# Kept as typed, but "Ron" and "ron" are the same person.
Index("ix_users_username_lower", func.lower(User.username), unique=True)


class UserPhoto(Base):
    """A person's photo, in its own table so signing in does not load it."""

    __tablename__ = "user_photos"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(20))
    # Either the bytes are here, or they are in S3 under s3_key and this is empty (see storage.py).
    data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    s3_key: Mapped[str] = mapped_column(String(100), default="")


class Activity(Base):
    """One line in an account's log."""

    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(40))
    detail: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    """One alert in a person's inbox."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(String(300))
    item_id: Mapped[int | None] = mapped_column(default=None)  # not a foreign key: the item may be removed
    person_id: Mapped[int | None] = mapped_column(default=None)  # who a friend alert is about
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(String(1000))
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Friendship(Base):
    """A friend request, and once accepted, the friendship. One row for the two people."""

    __tablename__ = "friendships"
    __table_args__ = (CheckConstraint("requester_id <> addressee_id", name="no_befriending_yourself"),)

    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)
    accepted: Mapped[bool] = mapped_column(default=False)


class Update(Base):
    """News for everyone: a system note (from the code) or an admin's message."""

    __tablename__ = "updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str | None] = mapped_column(String(40), unique=True, default=None)  # system notes only
    kind: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(String(1000))
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UpdateRead(Base):
    """How far each person has read."""

    __tablename__ = "update_reads"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    last_id: Mapped[int] = mapped_column(default=0)


class Block(Base):
    """One person blocking another: no friend requests or messages between them."""

    __tablename__ = "blocks"

    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True, index=True)


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
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)  # who added it
    # Empty for items added before this was recorded.
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow)
    images: Mapped[list["ItemImage"]] = relationship(
        lazy="selectin", order_by="[ItemImage.position, ItemImage.id]", cascade="all, delete-orphan"
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
    position: Mapped[int] = mapped_column(default=0)  # the lowest is the main picture
    s3_key: Mapped[str] = mapped_column(String(100), default="")  # set when the bytes are in S3, not in data


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
