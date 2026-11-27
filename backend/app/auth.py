from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import storage
from .activity import record
from .db import get_db
from .images import image_type, uploaded_bytes
from .inbox import notify
from .models import STAFF, Activity, User, UserPhoto
from .schemas import (
    ActivityOut,
    EmailIn,
    LoginIn,
    MeOut,
    PasswordIn,
    PermissionsIn,
    ProfileIn,
    TokenOut,
    UserIn,
    UserOut,
)
from .security import create_token, current_user, hash_password, require_admin, verify_password

router = APIRouter(prefix="/api")


def _by_username(username: str):
    return select(User).where(func.lower(User.username) == username.lower())


def _check_username_free(db: Session, username: str, user_id: int | None = None) -> None:
    holder = db.scalar(_by_username(username))
    if holder and holder.id != user_id:
        raise HTTPException(409, "That username is taken")


def _create_staff(db: Session, body: UserIn, created_by: str) -> User:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "That email already has an account")
    _check_username_free(db, body.username)
    user = User(
        email=email,
        username=body.username,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        role=STAFF,
    )
    db.add(user)
    db.flush()
    record(db, user.id, "account_created", created_by)
    db.commit()
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    login = body.login.strip()
    by_email = select(User).where(User.email == login.lower())
    user = db.scalar(by_email if "@" in login else _by_username(login))
    if user is None or not verify_password(body.password, user.password_hash):
        if user is not None:  # what was typed is never written down
            record(db, user.id, "sign_in_failed")
            db.commit()
        raise HTTPException(401, "Wrong sign-in details")  # one message, so accounts cannot be probed
    record(db, user.id, "sign_in")
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(body: UserIn, db: Session = Depends(get_db)):
    """Public sign-up. The new account is always staff: the role cannot be chosen."""
    user = _create_staff(db, body, "registered")
    return TokenOut(access_token=create_token(user.id))


@router.get("/auth/me", response_model=MeOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/auth/me", response_model=MeOut)
def update_profile(body: ProfileIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if body.name is not None:
        user.name = body.name.strip()
    if body.bio is not None:
        user.bio = body.bio.strip()
    if body.chat_from is not None:
        user.chat_from = body.chat_from
    if body.username:
        _check_username_free(db, body.username, user.id)
        user.username = body.username
    record(db, user.id, "profile_changed", ", ".join(sorted(body.model_fields_set)))
    db.commit()
    return user


@router.get("/auth/photo")
def get_photo(db: Session = Depends(get_db), user: User = Depends(current_user)):
    photo = db.get(UserPhoto, user.id)
    if photo is None:
        raise HTTPException(404, "You have no photo")
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    return Response(storage.read(photo), media_type=photo.content_type, headers=headers)


@router.put("/auth/photo", response_model=MeOut)
def put_photo(
    data: bytes = Depends(uploaded_bytes), db: Session = Depends(get_db), user: User = Depends(current_user)
):
    content_type = image_type(data)
    if content_type is None:
        raise HTTPException(415, "The image must be a PNG, JPEG or WebP file")
    photo = db.get(UserPhoto, user.id) or UserPhoto(user_id=user.id)
    old_key = photo.s3_key
    photo.content_type = content_type
    storage.store(photo, f"people/{user.id}", data, content_type)
    db.add(photo)
    user.photo_version += 1
    record(db, user.id, "profile_changed", "photo")
    db.commit()
    storage.discard(old_key)
    return user


@router.delete("/auth/photo", response_model=MeOut)
def delete_photo(db: Session = Depends(get_db), user: User = Depends(current_user)):
    photo = db.get(UserPhoto, user.id)
    key = photo.s3_key if photo else ""
    if photo is not None:
        db.delete(photo)
    user.photo_version = 0
    record(db, user.id, "profile_changed", "photo removed")
    db.commit()
    storage.discard(key)
    return user


@router.post("/auth/password", status_code=204)
def change_password(body: PasswordIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "The current password is wrong")
    user.password_hash = hash_password(body.new_password)
    record(db, user.id, "password_changed")
    db.commit()


@router.post("/auth/email", status_code=204)
def change_email(body: EmailIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """The email signs you in, so changing it needs the password. It is still never sent back."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "The current password is wrong")
    email = body.new_email.lower()
    holder = db.scalar(select(User).where(User.email == email))
    if holder and holder.id != user.id:
        raise HTTPException(409, "That email already has an account")
    user.email = email
    record(db, user.id, "email_changed")
    db.commit()


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(func.lower(User.username))).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = _create_staff(db, body, f"by {admin.username}")
    record(db, admin.id, "created_account", user.username)
    db.commit()
    return user


def _account_or_404(db: Session, user_id: int) -> User:
    account = db.get(User, user_id)
    if account is None:
        raise HTTPException(404, "No such account")
    return account


PERMISSIONS = {"can_add_items": "add items", "can_move_stock": "stock in/out", "can_edit_items": "edit items"}


@router.get("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_account(user_id: int, db: Session = Depends(get_db)):
    return _account_or_404(db, user_id)


@router.patch("/users/{user_id}/permissions", response_model=UserOut)
def change_permissions(
    user_id: int, body: PermissionsIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    account = _account_or_404(db, user_id)
    changes = {k: v for k, v in body.model_dump(exclude_none=True).items() if getattr(account, k) != v}
    if "role" in changes and account.id == admin.id:
        raise HTTPException(400, "You cannot change your own role")
    for field, value in changes.items():
        setattr(account, field, value)
    if changes:
        words = [
            f"role {value}" if field == "role" else f"{PERMISSIONS[field]} {'on' if value else 'off'}"
            for field, value in changes.items()
        ]
        record(db, account.id, "permissions_changed", f"by {admin.username}: {', '.join(words)}")
        record(db, admin.id, "changed_permissions", f"of {account.username}: {', '.join(words)}")
        notify(db, account.id, "permissions_changed", f"{admin.username} changed your permissions: {', '.join(words)}")
        db.commit()
    return account


@router.get("/users/{user_id}/activity", response_model=list[ActivityOut], dependencies=[Depends(require_admin)])
def activity_log(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    before: int | None = None,
    db: Session = Depends(get_db),
):
    """Newest first. `before` is the last id already seen, to fetch older entries."""
    _account_or_404(db, user_id)
    query = select(Activity).where(Activity.user_id == user_id).order_by(Activity.id.desc()).limit(limit)
    if before is not None:
        query = query.where(Activity.id < before)
    return db.scalars(query).all()
