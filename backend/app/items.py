from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .db import get_db
from .models import Item, Movement, User
from .schemas import ItemIn, ItemOut, MovementIn, MovementOut
from .security import current_user, require_admin

router = APIRouter(prefix="/api/items", dependencies=[Depends(current_user)])


def _item_or_404(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "No such item")
    return item


@router.get("", response_model=list[ItemOut])
def list_items(low: bool = False, db: Session = Depends(get_db)):
    query = select(Item).order_by(Item.name)
    if low:
        query = query.where(Item.quantity <= Item.reorder_level)
    return db.scalars(query).all()


@router.post("", response_model=ItemOut, status_code=201, dependencies=[Depends(require_admin)])
def create_item(body: ItemIn, db: Session = Depends(get_db)):
    if db.scalar(select(Item).where(Item.sku == body.sku)):
        raise HTTPException(409, "That SKU already exists")
    item = Item(**body.model_dump())
    db.add(item)
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
