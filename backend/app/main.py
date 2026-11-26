from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from . import auth, items
from .config import get_settings
from .db import Base, get_engine, new_session
from .models import ADMIN, User
from .security import hash_password


def seed_admin(session) -> bool:
    """Create the first admin from the environment. Does nothing once any user exists."""
    settings = get_settings()
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD) or session.scalar(select(User)):
        return False
    password_hash = hash_password(settings.ADMIN_PASSWORD)
    session.add(User(email=settings.ADMIN_EMAIL.lower(), password_hash=password_hash, role=ADMIN))
    session.commit()
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(get_engine())
    with new_session() as session:
        seed_admin(session)
    yield


app = FastAPI(title="Inventory", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(items.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
