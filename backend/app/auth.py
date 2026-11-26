from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import STAFF, User
from .schemas import LoginIn, PasswordIn, ProfileIn, TokenOut, UserIn, UserOut
from .security import create_token, current_user, hash_password, require_admin, verify_password

router = APIRouter(prefix="/api")


def _by_username(username: str):
    return select(User).where(func.lower(User.username) == username.lower())


def _check_username_free(db: Session, username: str, user_id: int | None = None) -> None:
    holder = db.scalar(_by_username(username))
    if holder and holder.id != user_id:
        raise HTTPException(409, "That username is taken")


def _create_staff(db: Session, body: UserIn) -> User:
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
    db.commit()
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    login = body.login.strip()
    by_email = select(User).where(User.email == login.lower())
    user = db.scalar(by_email if "@" in login else _by_username(login))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong sign-in details")  # one message, so accounts cannot be probed
    return TokenOut(access_token=create_token(user.id))


@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(body: UserIn, db: Session = Depends(get_db)):
    """Public sign-up. The new account is always staff: the role cannot be chosen."""
    user = _create_staff(db, body)
    return TokenOut(access_token=create_token(user.id))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/auth/me", response_model=UserOut)
def update_profile(body: ProfileIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    user.name = body.name.strip()
    if body.username:
        _check_username_free(db, body.username, user.id)
        user.username = body.username
    db.commit()
    return user


@router.post("/auth/password", status_code=204)
def change_password(body: PasswordIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "The current password is wrong")
    user.password_hash = hash_password(body.new_password)
    db.commit()


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(func.lower(User.username))).all()


@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(body: UserIn, db: Session = Depends(get_db)):
    return _create_staff(db, body)
