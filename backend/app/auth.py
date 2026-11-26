from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import STAFF, User
from .schemas import LoginIn, TokenOut, UserIn, UserOut
from .security import create_token, current_user, hash_password, require_admin, verify_password

router = APIRouter(prefix="/api")


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")  # same message for both, so emails cannot be probed
    return TokenOut(access_token=create_token(user.id))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(body: UserIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "That email already has an account")
    user = User(email=email, password_hash=hash_password(body.password), role=STAFF)
    db.add(user)
    db.commit()
    return user
