"""What each account has done, for admins to read. Names of things, never passwords, emails or what was typed."""
from sqlalchemy.orm import Session

from .models import Activity


def record(db: Session, user_id: int, action: str, detail: str = "") -> None:
    """Adds one line to a person's log. The caller commits, so it is saved together with what it describes."""
    db.add(Activity(user_id=user_id, action=action, detail=detail[:300]))


def named(item) -> str:
    return f"{item.name} (ID {item.id})"
