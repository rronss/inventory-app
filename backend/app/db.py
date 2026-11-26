from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    url = get_settings().DATABASE_URL
    options = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    return create_engine(url, **options)


def new_session() -> Session:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)()


def get_db():
    session = new_session()
    try:
        yield session
    finally:
        session.close()
