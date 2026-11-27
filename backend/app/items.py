from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, joinedload

from . import storage
from .activity import named, record
from .db import get_db
from .inbox import item_changed, item_removed, stock_moved
from .models import ADMIN, Item, Movement, User
from .privacy import can_see_history, can_see_stock, item_view
from .schemas import ExploreItemOut, ItemEditIn, ItemIn, ItemOut, MovementIn, MovementOut, RecentMovementOut
from .security import check_hands_on, current_user, may_add_items, may_edit_items, may_move_stock, require_admin

router = APIRouter(prefix="/api/items", dependencies=[Depends(current_user)])
movements_router = APIRouter(prefix="/api/movements", dependencies=[Depends(current_user)])
explore_router = APIRouter(prefix="/api/explore", dependencies=[Depends(current_user)])


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
    check_hands_on(item, user)
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
        what = ", ".join(changed).replace("_", " ")
        record(db, user.id, "item_edited", f"{named(item)}: {what}")
        item_changed(db, item, user, what)
    db.commit()
    return item_view(item, user)


@router.delete("/{item_id}", status_code=204)
def remove_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """Removes the item for good, with its pictures and its movements. There is no undo."""
    item = item_or_404(db, item_id)
    record(db, user.id, "item_removed", f"{named(item)}, SKU {item.sku}")
    item_removed(db, item, user)
    db.execute(delete(Movement).where(Movement.item_id == item_id))
    keys = [picture.s3_key for picture in item.images]
    db.delete(item)  # the pictures go with it
    db.commit()
    storage.discard(*keys)


@router.post("/{item_id}/movements", response_model=ItemOut)
def move_stock(item_id: int, body: MovementIn, db: Session = Depends(get_db), user: User = Depends(may_move_stock)):
    # Not for private stock: "Not enough stock" would let anyone work out the quantity.
    item = item_or_404(db, item_id)
    check_hands_on(item, user)
    if not can_see_stock(item, user):
        raise HTTPException(403, "The stock of this item is private")
    was_low, was_empty = item.low_stock, item.quantity == 0
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
    moved = db.get(Item, item_id, populate_existing=True)  # with its new quantity
    record(db, user.id, action, f"{body.change:+d} {named(moved)}{note}")
    stock_moved(db, moved, user, body.change, was_low, was_empty)
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


@explore_router.get("", response_model=list[ExploreItemOut])
def explore(db: Session = Depends(get_db), me: User = Depends(current_user)):
    """Every public item, yours included, newest first. An item whose stock is private is not listed here."""
    query = (
        select(Item, User)
        .outerjoin(User, Item.creator_id == User.id)
        .where(Item.stock_private.is_(False))
        .order_by(Item.id.desc())
    )
    return [
        ExploreItemOut(
            **item_view(item, me).model_dump(),
            added_by_id=person.id if person else None,
            added_by=person.username if person else None,
            added_by_photo_version=person.photo_version if person else None,
            created_at=item.created_at,
        )
        for item, person in db.execute(query)
    ]
