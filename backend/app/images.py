"""A few pictures per item. storage.py decides whether the files are kept in the database or in S3."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from . import storage
from .activity import named, record
from .db import get_db
from .inbox import item_changed
from .items import item_or_404
from .models import ItemImage, User
from .privacy import item_view
from .schemas import ImageOrderIn, ItemOut
from .security import current_user, may_edit_items

MAX_IMAGE_BYTES = 2 * 1024 * 1024  # nginx.conf allows a little more, so this message is the one people see
MAX_IMAGES = 5

router = APIRouter(prefix="/api/items/{item_id}/images", dependencies=[Depends(current_user)])


def image_type(data: bytes) -> str | None:
    """Read from the file itself: the browser's Content-Type is only a claim. No SVG, which can run scripts."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


async def uploaded_bytes(request: Request) -> bytes:
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "The image must be 2 MB or smaller")
    return bytes(data)


def _image_or_404(db: Session, item_id: int, image_id: int) -> ItemImage:
    image = db.get(ItemImage, image_id)
    if image is None or image.item_id != item_id:
        raise HTTPException(404, "No such image")
    return image


@router.get("/{image_id}")
def get_image(item_id: int, image_id: int, db: Session = Depends(get_db)):
    image = _image_or_404(db, item_id, image_id)
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    return Response(storage.read(image), media_type=image.content_type, headers=headers)


@router.post("", response_model=ItemOut, status_code=201)
def add_image(
    item_id: int,
    data: bytes = Depends(uploaded_bytes),
    db: Session = Depends(get_db),
    user: User = Depends(may_edit_items),
):
    item = item_or_404(db, item_id)
    content_type = image_type(data)
    if content_type is None:
        raise HTTPException(415, "The image must be a PNG, JPEG or WebP file")
    if len(item.images) >= MAX_IMAGES:
        raise HTTPException(409, f"An item can have {MAX_IMAGES} images")
    last = max((image.position for image in item.images), default=-1)
    picture = ItemImage(content_type=content_type, position=last + 1)
    storage.store(picture, f"items/{item.id}", data, content_type)
    item.images.append(picture)
    record(db, user.id, "image_added", named(item))
    item_changed(db, item, user, "pictures")
    db.commit()
    return item_view(item, user)


@router.put("/order", response_model=ItemOut)
def arrange_images(
    item_id: int, body: ImageOrderIn, db: Session = Depends(get_db), user: User = Depends(may_edit_items)
):
    """The item's pictures in the order to show them. The first is the main one."""
    item = item_or_404(db, item_id)
    if sorted(body.image_ids) != sorted(item.image_ids):
        raise HTTPException(422, "List each of this item's images once")
    if body.image_ids != item.image_ids:
        for image in item.images:
            image.position = body.image_ids.index(image.id)
        record(db, user.id, "image_reordered", named(item))
        item_changed(db, item, user, "pictures")
        db.commit()
        db.expire(item, ["images"])  # read them again in their new order
    return item_view(item, user)


@router.delete("/{image_id}", response_model=ItemOut)
def delete_image(item_id: int, image_id: int, db: Session = Depends(get_db), user: User = Depends(may_edit_items)):
    item = item_or_404(db, item_id)
    picture = _image_or_404(db, item_id, image_id)
    key = picture.s3_key
    item.images.remove(picture)
    record(db, user.id, "image_removed", named(item))
    item_changed(db, item, user, "pictures")
    db.commit()
    storage.discard(key)
    return item_view(item, user)
