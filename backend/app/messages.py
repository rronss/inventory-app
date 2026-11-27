"""Messages between two people.

Every query starts from the signed-in person, so nobody, admins included, can read a conversation they are not in.
Messages are not written to the activity log.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from .db import get_db
from .friends import are_friends, blocked
from .models import Message, User
from .schemas import ConversationOut, MessageIn, MessageOut, PersonOut
from .security import current_user

router = APIRouter(prefix="/api/messages", dependencies=[Depends(current_user)])
SHOWN = 100  # the most recent messages of a conversation


def _other_or_404(db: Session, person_id: int, me: User) -> User:
    person = db.get(User, person_id)
    if person is None:
        raise HTTPException(404, "No such person")
    if person.id == me.id:
        raise HTTPException(400, "You cannot message yourself")
    return person


def _view(message: Message, me: User) -> MessageOut:
    return MessageOut(id=message.id, text=message.text, mine=message.sender_id == me.id, created_at=message.created_at)


@router.get("", response_model=list[ConversationOut])
def conversations(db: Session = Depends(get_db), me: User = Depends(current_user)):
    """One line per person you have written with, the most recent first."""
    query = select(Message).where(or_(Message.sender_id == me.id, Message.recipient_id == me.id))
    latest: dict[int, Message] = {}
    waiting: dict[int, int] = {}
    for message in db.scalars(query.order_by(Message.id.desc())):
        other = message.recipient_id if message.sender_id == me.id else message.sender_id
        latest.setdefault(other, message)
        if message.recipient_id == me.id and not message.is_read:
            waiting[other] = waiting.get(other, 0) + 1
    people = {person.id: person for person in db.scalars(select(User).where(User.id.in_(latest)))}
    return [
        ConversationOut(
            person=PersonOut.model_validate(people[other]),
            last_text=message.text,
            last_mine=message.sender_id == me.id,
            last_at=message.created_at,
            unread=waiting.get(other, 0),
        )
        for other, message in latest.items()
    ]


@router.get("/{person_id}", response_model=list[MessageOut])
def conversation(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    other = _other_or_404(db, person_id, me)
    between = or_(
        and_(Message.sender_id == me.id, Message.recipient_id == other.id),
        and_(Message.sender_id == other.id, Message.recipient_id == me.id),
    )
    newest = db.scalars(select(Message).where(between).order_by(Message.id.desc()).limit(SHOWN)).all()
    return [_view(message, me) for message in reversed(newest)]


@router.post("/{person_id}", response_model=MessageOut, status_code=201)
def send(person_id: int, body: MessageIn, db: Session = Depends(get_db), me: User = Depends(current_user)):
    other = _other_or_404(db, person_id, me)
    if blocked(db, me.id, other.id):
        raise HTTPException(403, "You can't send messages to this person")
    if other.chat_from == "friends" and not are_friends(db, me.id, other.id):
        raise HTTPException(403, f"{other.username} only accepts messages from friends")
    message = Message(sender_id=me.id, recipient_id=other.id, text=body.text)
    db.add(message)
    db.commit()
    return _view(message, me)


@router.post("/{person_id}/read", status_code=204)
def mark_read(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    other = _other_or_404(db, person_id, me)
    db.execute(update(Message).where(Message.sender_id == other.id, Message.recipient_id == me.id).values(is_read=True))
    db.commit()
