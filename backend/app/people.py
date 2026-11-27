"""A person's record, so colleagues can recognise them: who they are and the items they added.

Visible to anyone signed in. Emails are never part of it, and private stock stays hidden from non-admins.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Friendship, Item, User, UserPhoto
from .privacy import item_view
from .schemas import ItemOut, PersonOut, PersonRecordOut
from .security import current_user

router = APIRouter(prefix="/api/people", dependencies=[Depends(current_user)])


def _person_or_404(db: Session, person_id: int) -> User:
    person = db.get(User, person_id)
    if person is None:
        raise HTTPException(404, "No such person")
    return person


@router.get("", response_model=list[PersonOut])
def everyone(db: Session = Depends(get_db)):
    """Who there is, to pick someone to write to."""
    return db.scalars(select(User).order_by(func.lower(User.username))).all()


@router.get("/{person_id}", response_model=PersonRecordOut)
def person_record(person_id: int, db: Session = Depends(get_db)):
    person = _person_or_404(db, person_id)
    theirs = or_(Friendship.requester_id == person.id, Friendship.addressee_id == person.id)
    friends = db.scalar(select(func.count()).select_from(Friendship).where(Friendship.accepted.is_(True), theirs))
    return PersonRecordOut(**PersonOut.model_validate(person).model_dump(), friends=friends)


@router.get("/{person_id}/photo")
def photo(person_id: int, db: Session = Depends(get_db)):
    found = db.get(UserPhoto, person_id)
    if found is None:
        raise HTTPException(404, "No photo")
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    return Response(found.data, media_type=found.content_type, headers=headers)


@router.get("/{person_id}/items", response_model=list[ItemOut])
def items_added(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    _person_or_404(db, person_id)
    query = select(Item).where(Item.creator_id == person_id).order_by(Item.name)
    return [item_view(item, me) for item in db.scalars(query)]
