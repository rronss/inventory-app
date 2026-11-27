"""Alerts for one person, about the items they added and about their own account.

Nothing here may tell someone what the rest of the app hides from them: no stock levels for private stock, and no
changes for a private history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .activity import named
from .db import get_db
from .models import Item, Message, Notification, User
from .privacy import can_see_history, can_see_stock
from .schemas import NotificationOut, UnreadOut
from .security import current_user
from .updates import unread_count

router = APIRouter(prefix="/api/inbox", dependencies=[Depends(current_user)])


def notify(
    db: Session, user_id: int, kind: str, text: str, item_id: int | None = None, person_id: int | None = None
) -> None:
    """Puts one alert in a person's inbox. The caller commits, together with what the alert is about."""
    db.add(Notification(user_id=user_id, kind=kind, text=text[:300], item_id=item_id, person_id=person_id))


def stock_moved(db: Session, item: Item, actor: User, change: int, was_low: bool, was_empty: bool) -> None:
    """Called with the item as it is after the movement."""
    owner = db.get(User, item.creator_id) if item.creator_id else None
    if owner is None:
        return
    if owner.id != actor.id and can_see_history(item, owner):
        words = f"added {change} to" if change > 0 else f"took {-change} from"
        notify(db, owner.id, "stock_changed", f"{actor.username} {words} {named(item)}", item.id)
    if not can_see_stock(item, owner):
        return
    # Only on the way down, so an item that stays low does not alert again.
    if item.quantity == 0 and not was_empty:
        notify(db, owner.id, "out_of_stock", f"{named(item)} is out of stock", item.id)
    elif item.low_stock and not was_low:
        notify(db, owner.id, "low_stock", f"{named(item)} is low: {item.quantity} left", item.id)


def item_changed(db: Session, item: Item, actor: User, what: str) -> None:
    if item.creator_id and item.creator_id != actor.id:
        notify(db, item.creator_id, "item_edited", f"{actor.username} edited {named(item)}: {what}", item.id)


def item_removed(db: Session, item: Item, actor: User) -> None:
    if item.creator_id and item.creator_id != actor.id:
        notify(db, item.creator_id, "item_removed", f"{actor.username} removed {named(item)}")


@router.get("", response_model=list[NotificationOut])
def my_inbox(
    limit: int = Query(default=50, ge=1, le=100),
    before: int | None = None,
    db: Session = Depends(get_db),
    me: User = Depends(current_user),
):
    """Newest first. `before` is the last id already seen, to fetch older ones."""
    query = select(Notification).where(Notification.user_id == me.id).order_by(Notification.id.desc()).limit(limit)
    if before is not None:
        query = query.where(Notification.id < before)
    return db.scalars(query).all()


@router.get("/unread", response_model=UnreadOut)
def unread(db: Session = Depends(get_db), me: User = Depends(current_user)):
    alerts = select(func.count(Notification.id)).where(Notification.user_id == me.id, Notification.is_read.is_(False))
    messages = select(func.count(Message.id)).where(Message.recipient_id == me.id, Message.is_read.is_(False))
    return UnreadOut(unread=db.scalar(alerts), messages=db.scalar(messages), updates=unread_count(db, me))


@router.post("/read", status_code=204)
def read_all(db: Session = Depends(get_db), me: User = Depends(current_user)):
    db.execute(update(Notification).where(Notification.user_id == me.id).values(is_read=True))
    db.commit()


@router.post("/{notification_id}/read", status_code=204)
def read_one(notification_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    found = db.get(Notification, notification_id)
    if found is None or found.user_id != me.id:  # someone else's looks the same as none
        raise HTTPException(404, "No such alert")
    found.is_read = True
    db.commit()
