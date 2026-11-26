"""Who may see an item's stock and history. Every item sent to a browser goes through item_view.

SKU, ID, name, description and pictures are always visible to a signed-in user.
"""
from .models import ADMIN, Item, User
from .schemas import ItemOut


def can_see_stock(item: Item, user: User) -> bool:
    return user.role == ADMIN or not item.stock_private


def can_see_history(item: Item, user: User) -> bool:
    return user.role == ADMIN or not item.history_private


def item_view(item: Item, user: User) -> ItemOut:
    view = ItemOut.model_validate(item)
    if can_see_stock(item, user):
        return view
    return view.model_copy(update={"quantity": None, "reorder_level": None, "low_stock": None})
