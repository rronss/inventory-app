from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from ragbot.router import router as chat_router

from . import auth, friends, images, inbox, items, messages, people, updates
from .config import get_settings
from .db import Base, get_engine, new_session
from .models import ADMIN, User
from .security import hash_password
from .upgrade import add_missing_columns


def seed_admin(session) -> bool:
    """Create the first admin from the environment. Does nothing once any user exists."""
    settings = get_settings()
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD) or session.scalar(select(User)):
        return False
    password_hash = hash_password(settings.ADMIN_PASSWORD)
    session.add(User(email=settings.ADMIN_EMAIL.lower(), username="admin", password_hash=password_hash, role=ADMIN))
    session.commit()
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(get_engine())
    add_missing_columns(get_engine())
    with new_session() as session:
        seed_admin(session)
        updates.seed_updates(session)
    yield


app = FastAPI(title="Crate", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(items.router)
app.include_router(items.movements_router)
app.include_router(items.explore_router)
app.include_router(images.router)
app.include_router(people.router)
app.include_router(inbox.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(updates.router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
