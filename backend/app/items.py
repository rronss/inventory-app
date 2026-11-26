from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .models import ADMIN, Item, Movement, User
from .schemas import AssignIn, ItemIn, ItemOut, MovementIn, MovementOut
from .security import current_user, require_admin

router = APIRouter(prefix="/api/items", dependencies=[Depends(current_user)])


def _item_or_404(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "No such item")
    return item


@router.get("", response_model=list[ItemOut])
def list_items(
    low: bool = False, mine: bool = False, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    query = select(Item).order_by(Item.name)
    if mine:
        query = query.where(Item.owner_id == user.id)
    if low:
        query = query.where(Item.quantity <= Item.reorder_level)
    return db.scalars(query).all()


@router.post("", response_model=ItemOut, status_code=201)
def create_item(body: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if db.scalar(select(Item).where(Item.sku == body.sku)):
        raise HTTPException(409, "That SKU already exists")
    item = Item(**body.model_dump(), owner=user)
    db.add(item)
    db.commit()
    return item


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return _item_or_404(db, item_id)


@router.post("/{item_id}/attach", response_model=ItemOut)
def attach(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _item_or_404(db, item_id)
    # Claim it only if nobody has it (or you already do), in one statement, so two people cannot both succeed.
    claimed = db.execute(
        update(Item)
        .where(Item.id == item_id, (Item.owner_id.is_(None)) | (Item.owner_id == user.id))
        .values(owner_id=user.id)
    )
    if claimed.rowcount == 0:
        db.rollback()
        raise HTTPException(409, "Already attached to someone else")
    db.commit()
    return db.get(Item, item_id, populate_existing=True)


@router.post("/{item_id}/detach", response_model=ItemOut)
def detach(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = _item_or_404(db, item_id)
    if item.owner_id != user.id and user.role != ADMIN:
        raise HTTPException(403, "Only the owner or an admin can detach it")
    item.owner = None
    db.commit()
    return item


@router.put("/{item_id}/owner", response_model=ItemOut, dependencies=[Depends(require_admin)])
def assign(item_id: int, body: AssignIn, db: Session = Depends(get_db)):
    item = _item_or_404(db, item_id)
    owner = None
    if body.user_id is not None:
        owner = db.get(User, body.user_id)
        if owner is None:
            raise HTTPException(404, "No such user")
    item.owner = owner
    db.commit()
    return item


@router.post("/{item_id}/movements", response_model=ItemOut)
def move_stock(item_id: int, body: MovementIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _item_or_404(db, item_id)
    # One conditional UPDATE, so two removals at the same moment cannot take the stock below zero.
    changed = db.execute(
        update(Item)
        .where(Item.id == item_id, Item.quantity + body.change >= 0)
        .values(quantity=Item.quantity + body.change)
    )
    if changed.rowcount == 0:
        db.rollback()
        raise HTTPException(409, "Not enough stock")
    db.add(Movement(item_id=item_id, user_id=user.id, change=body.change, note=body.note))
    db.commit()
    return db.get(Item, item_id, populate_existing=True)


@router.get("/{item_id}/movements", response_model=list[MovementOut])
def history(item_id: int, db: Session = Depends(get_db)):
    _item_or_404(db, item_id)
    query = select(Movement).where(Movement.item_id == item_id).order_by(Movement.id.desc()).limit(50)
    return db.scalars(query).all()
