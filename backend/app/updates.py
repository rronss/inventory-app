"""Updates for everyone: notes about the app (written here, in the code) and messages posted by admins."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .activity import record
from .db import get_db
from .models import Update, UpdateRead, User
from .schemas import UpdateIn, UpdateOut
from .security import current_user, require_admin

router = APIRouter(prefix="/api/updates", dependencies=[Depends(current_user)])


def _day(month: int, day: int) -> datetime:
    return datetime(2026, month, day, 12, tzinfo=timezone.utc)


# Add a line here when something changes for the people who use the app. The key must never be reused.
SYSTEM_UPDATES = [
    ("item-pages", _day(11, 26), "Item pages", "Each item has a page with pictures, history and privacy."),
    ("profiles", _day(11, 26), "Profiles and permissions", "Profiles, staff permissions and an activity log."),
    ("explore", _day(11, 27), "Crate and Explore", "The app is now Crate. Explore shows every public item."),
    ("inbox", _day(11, 27), "Inbox", "Chats, alerts, friend requests and this Updates tab."),
]


def seed_updates(db: Session) -> int:
    """Stores any system update not stored yet. Returns how many were added."""
    known = set(db.scalars(select(Update.key).where(Update.key.is_not(None))))
    new = [entry for entry in SYSTEM_UPDATES if entry[0] not in known]
    for key, when, title, text in new:
        db.add(Update(key=key, kind="system", title=title, text=text, created_at=when))
    db.commit()
    return len(new)


def last_read(db: Session, user: User) -> int:
    found = db.get(UpdateRead, user.id)
    return found.last_id if found else 0


def unread_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count(Update.id)).where(Update.id > last_read(db, user)))


@router.get("", response_model=list[UpdateOut])
def updates(db: Session = Depends(get_db), me: User = Depends(current_user)):
    seen = last_read(db, me)
    query = (
        select(Update, User.username)
        .outerjoin(User, Update.author_id == User.id)
        .order_by(Update.created_at.desc(), Update.id.desc())
        .limit(100)
    )
    return [
        UpdateOut(
            id=entry.id,
            kind=entry.kind,
            title=entry.title,
            text=entry.text,
            author=author,
            created_at=entry.created_at,
            unread=entry.id > seen,
        )
        for entry, author in db.execute(query)
    ]


@router.post("", response_model=UpdateOut, status_code=201)
def post_message(body: UpdateIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    entry = Update(kind="admin", title=body.title, text=body.text, author_id=admin.id)
    db.add(entry)
    record(db, admin.id, "announcement_posted", body.title)
    db.commit()
    return UpdateOut(
        id=entry.id,
        kind=entry.kind,
        title=entry.title,
        text=entry.text,
        author=admin.username,
        created_at=entry.created_at,
        unread=True,
    )


@router.post("/read", status_code=204)
def mark_read(db: Session = Depends(get_db), me: User = Depends(current_user)):
    newest = db.scalar(select(func.max(Update.id))) or 0
    db.merge(UpdateRead(user_id=me.id, last_id=newest))
    db.commit()


@router.delete("/{update_id}", status_code=204)
def remove_message(update_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    entry = db.get(Update, update_id)
    if entry is None:
        raise HTTPException(404, "No such update")
    if entry.kind != "admin":
        raise HTTPException(400, "System updates cannot be removed")
    record(db, admin.id, "announcement_removed", entry.title)
    db.delete(entry)
    db.commit()
