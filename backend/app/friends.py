"""Friend requests and blocking. A person sees only their own lists, and being friends unlocks nothing hidden.

Nobody is told that they were blocked: to them the status stays "none", and sending is simply refused.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from .db import get_db
from .inbox import notify
from .models import Block, Friendship, Notification, User
from .schemas import FriendsOut, FriendStatusOut, PersonOut
from .security import current_user

router = APIRouter(prefix="/api/friends", dependencies=[Depends(current_user)])


def _other_or_404(db: Session, person_id: int, me: User) -> User:
    person = db.get(User, person_id)
    if person is None:
        raise HTTPException(404, "No such person")
    if person.id == me.id:
        raise HTTPException(400, "You cannot befriend yourself")
    return person


def _between(db: Session, one: int, two: int) -> Friendship | None:
    """The request or friendship of two people, whoever asked."""
    either_way = or_(
        and_(Friendship.requester_id == one, Friendship.addressee_id == two),
        and_(Friendship.requester_id == two, Friendship.addressee_id == one),
    )
    return db.scalar(select(Friendship).where(either_way))


def blocked(db: Session, one: int, two: int) -> bool:
    """Whether either of the two has blocked the other."""
    return db.get(Block, (one, two)) is not None or db.get(Block, (two, one)) is not None


def are_friends(db: Session, one: int, two: int) -> bool:
    found = _between(db, one, two)
    return found is not None and found.accepted


def _status(found: Friendship | None, me: User) -> FriendStatusOut:
    if found is None:
        return FriendStatusOut(status="none")
    if found.accepted:
        return FriendStatusOut(status="friends")
    return FriendStatusOut(status="sent" if found.requester_id == me.id else "received")


def _accept(db: Session, found: Friendship, me: User) -> None:
    found.accepted = True
    notify(db, found.requester_id, "friend_accepted", f"{me.username} accepted your friend request", person_id=me.id)
    # the request in my inbox has been dealt with
    db.execute(
        update(Notification)
        .where(Notification.user_id == me.id, Notification.person_id == found.requester_id)
        .values(is_read=True)
    )


@router.get("", response_model=FriendsOut)
def my_friends(db: Session = Depends(get_db), me: User = Depends(current_user)):
    mine = db.scalars(
        select(Friendship).where(or_(Friendship.requester_id == me.id, Friendship.addressee_id == me.id))
    ).all()
    ids = {row.addressee_id if row.requester_id == me.id else row.requester_id for row in mine}
    people = {person.id: person for person in db.scalars(select(User).where(User.id.in_(ids)))}
    lists = {"friends": [], "incoming": [], "outgoing": [], "blocked": []}
    for row in mine:
        other = people[row.addressee_id if row.requester_id == me.id else row.requester_id]
        key = "friends" if row.accepted else "outgoing" if row.requester_id == me.id else "incoming"
        lists[key].append(PersonOut.model_validate(other))
    mine_blocked = select(User).join(Block, Block.blocked_id == User.id).where(Block.blocker_id == me.id)
    lists["blocked"] = [PersonOut.model_validate(person) for person in db.scalars(mine_blocked)]
    return FriendsOut(**{key: sorted(rows, key=lambda p: p.username.lower()) for key, rows in lists.items()})


@router.get("/{person_id}", response_model=FriendStatusOut)
def status(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    other = _other_or_404(db, person_id, me)
    if db.get(Block, (me.id, other.id)):
        return FriendStatusOut(status="blocked")
    return _status(_between(db, me.id, other.id), me)


@router.post("/{person_id}", response_model=FriendStatusOut)
def ask(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    """Sends a request. If they already asked you, this accepts theirs. Asking twice changes nothing."""
    other = _other_or_404(db, person_id, me)
    if blocked(db, me.id, other.id):
        raise HTTPException(403, "You can't send a request to this person")
    found = _between(db, me.id, other.id)
    if found is None:
        found = Friendship(requester_id=me.id, addressee_id=other.id, accepted=False)
        db.add(found)
        notify(db, other.id, "friend_request", f"{me.username} sent you a friend request", person_id=me.id)
    elif not found.accepted and found.requester_id == other.id:
        _accept(db, found, me)
    db.commit()
    return _status(found, me)


@router.post("/{person_id}/accept", response_model=FriendStatusOut)
def accept(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    found = _between(db, me.id, _other_or_404(db, person_id, me).id)
    if found is None or found.accepted or found.addressee_id != me.id:  # only the one asked can accept
        raise HTTPException(404, "No request from this person")
    _accept(db, found, me)
    db.commit()
    return _status(found, me)


@router.delete("/{person_id}", response_model=FriendStatusOut)
def end(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    """Declines or cancels a request, or removes a friend."""
    other = _other_or_404(db, person_id, me)
    found = _between(db, me.id, other.id)
    if found is not None:
        db.delete(found)
        db.execute(
            update(Notification)
            .where(Notification.user_id == me.id, Notification.person_id == other.id)
            .values(is_read=True)
        )
        db.commit()
    return FriendStatusOut(status="none")


@router.put("/{person_id}/block", response_model=FriendStatusOut)
def block(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    """Ends any friendship or request between the two, and stops new ones and messages."""
    other = _other_or_404(db, person_id, me)
    if db.get(Block, (me.id, other.id)) is None:
        db.add(Block(blocker_id=me.id, blocked_id=other.id))
    found = _between(db, me.id, other.id)
    if found is not None:
        db.delete(found)
    db.execute(
        update(Notification)
        .where(Notification.user_id == me.id, Notification.person_id == other.id)
        .values(is_read=True)
    )
    db.commit()
    return FriendStatusOut(status="blocked")


@router.delete("/{person_id}/block", response_model=FriendStatusOut)
def unblock(person_id: int, db: Session = Depends(get_db), me: User = Depends(current_user)):
    other = _other_or_404(db, person_id, me)
    found = db.get(Block, (me.id, other.id))
    if found is not None:
        db.delete(found)
        db.commit()
    return _status(_between(db, me.id, other.id), me)

