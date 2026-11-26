from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, joinedload

from .activity import named, record
from .db import get_db
from .models import ADMIN, Item, Movement, User
from .privacy import can_see_history, can_see_stock, item_view
from .schemas import ItemEditIn, ItemIn, ItemOut, MovementIn, MovementOut, RecentMovementOut
from .security import current_user, may_add_items, may_edit_items, may_move_stock, require_admin

router = APIRouter(prefix="/api/items", dependencies=[Depends(current_user)])
movements_router = APIRouter(prefix="/api/movements", dependencies=[Depends(current_user)])


def item_or_404(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(404, "No such item")
    return item


@router.get("", response_model=list[ItemOut])
def list_items(low: bool = False, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = select(Item).order_by(Item.name)
    if low:
        query = query.where(Item.quantity <= Item.reorder_level)
        if user.role != ADMIN:
            query = query.where(Item.stock_private.is_(False))  # the filter must not give it away
    return [item_view(item, user) for item in db.scalars(query)]


@router.post("", response_model=ItemOut, status_code=201)
def create_item(body: ItemIn, db: Session = Depends(get_db), user: User = Depends(may_add_items)):
    if db.scalar(select(Item).where(Item.sku == body.sku)):
        raise HTTPException(409, "That SKU already exists")
    item = Item(**body.model_dump(), creator_id=user.id)
    db.add(item)
    db.flush()  # gives the item its ID, for the log
    record(db, user.id, "item_added", named(item))
    db.commit()
    return item_view(item, user)


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return item_view(item_or_404(db, item_id), user)


@router.patch("/{item_id}", response_model=ItemOut)
def edit_item(item_id: int, body: ItemEditIn, db: Session = Depends(get_db), user: User = Depends(may_edit_items)):
    item = item_or_404(db, item_id)
    changes = body.model_dump(exclude_none=True)
    if {"stock_private", "history_private"} & changes.keys() and user.role != ADMIN:
        raise HTTPException(403, "Only an admin can make information public or private")
    if "reorder_level" in changes and not can_see_stock(item, user):
        raise HTTPException(403, "The stock of this item is private")
    sku = changes.get("sku", item.sku)
    if sku != item.sku and db.scalar(select(Item).where(Item.sku == sku)):
        raise HTTPException(409, "That SKU already exists")
    if "description" in changes:
        changes["description"] = changes["description"].strip()
    changed = [field for field, value in changes.items() if getattr(item, field) != value]
    for field, value in changes.items():
        setattr(item, field, value)
    if changed:
        record(db, user.id, "item_edited", f"{named(item)}: {', '.join(changed).replace('_', ' ')}")
    db.commit()
    return item_view(item, user)


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Removes the item for good, with its pictures and its movements. There is no undo."""
    item = item_or_404(db, item_id)
    record(db, user.id, "item_removed", f"{named(item)}, SKU {item.sku}")
    db.execute(delete(Movement).where(Movement.item_id == item_id))
    db.delete(item)  # the pictures go with it
    db.commit()


@router.post("/{item_id}/movements", response_model=ItemOut)
def move_stock(item_id: int, body: MovementIn, db: Session = Depends(get_db), user: User = Depends(may_move_stock)):
    # Not for private stock: "Not enough stock" would let anyone work out the quantity.
    if not can_see_stock(item_or_404(db, item_id), user):
        raise HTTPException(403, "The stock of this item is private")
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
    note = f": {body.note}" if body.note else ""
    action = "stock_in" if body.change > 0 else "stock_out"
    record(db, user.id, action, f"{body.change:+d} {named(db.get(Item, item_id))}{note}")
    db.commit()
    return item_view(db.get(Item, item_id, populate_existing=True), user)


@router.get("/{item_id}/movements", response_model=list[MovementOut])
def history(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not can_see_history(item_or_404(db, item_id), user):
        raise HTTPException(403, "The stock history of this item is private")
    query = select(Movement).where(Movement.item_id == item_id).order_by(Movement.id.desc()).limit(50)
    return db.scalars(query).all()


@movements_router.get("", response_model=list[RecentMovementOut])
def recent_movements(
    limit: int = Query(default=50, ge=1, le=100),
    before: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Every item's movements, newest first. `before` is the last id already seen, to fetch older ones."""
    query = select(Movement).options(joinedload(Movement.item)).order_by(Movement.id.desc()).limit(limit)
    if before is not None:
        query = query.where(Movement.id < before)
    if user.role != ADMIN:
        query = query.where(Movement.item.has(Item.history_private.is_(False)))
    return db.scalars(query).all()
