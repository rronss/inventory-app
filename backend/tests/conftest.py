import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-only-key-that-is-long-enough-0123456789")
os.environ["PICTURE_STORAGE"] = "db"  # never a real bucket, whatever the shell has set

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ADMIN, STAFF, User  # noqa: E402
from app.security import create_token, hash_password  # noqa: E402

PASSWORD = "test-password-1"


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        yield db


@pytest.fixture
def client(session):
    app.dependency_overrides[get_db] = lambda: session
    yield TestClient(app)  # no "with": the startup hook would open the real database
    app.dependency_overrides.clear()


def _user(session, email: str, role: str) -> User:
    user = User(email=email, username=email.split("@")[0], password_hash=hash_password(PASSWORD), role=role)
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def admin(session):
    return _user(session, "admin@example.com", ADMIN)


@pytest.fixture
def staff(session):
    return _user(session, "staff@example.com", STAFF)


@pytest.fixture
def as_admin(admin):
    return {"Authorization": f"Bearer {create_token(admin.id)}"}


@pytest.fixture
def as_staff(staff):
    return {"Authorization": f"Bearer {create_token(staff.id)}"}
