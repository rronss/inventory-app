import pytest
from conftest import PASSWORD
from pydantic import ValidationError

from app.config import Settings
from app.main import seed_admin


def test_login_returns_a_token_that_works(client, admin):
    response = client.post("/api/auth/login", json={"email": "ADMIN@example.com", "password": PASSWORD})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "admin"


@pytest.mark.parametrize("email, password", [("admin@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)])
def test_wrong_credentials_get_the_same_answer(client, admin, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401 and response.json()["detail"] == "Wrong email or password"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-token"}])
def test_pages_need_a_valid_token(client, headers):
    assert client.get("/api/items", headers=headers).status_code == 401


def test_there_is_no_public_sign_up(client):
    body = {"email": "intruder@example.com", "password": "long-enough-1"}
    assert client.post("/api/users", json=body).status_code == 401
    assert client.post("/api/auth/register", json=body).status_code == 404


def test_only_an_admin_can_add_users(client, as_staff, as_admin):
    body = {"email": "new@example.com", "password": "long-enough-1"}
    assert client.post("/api/users", json=body, headers=as_staff).status_code == 403
    created = client.post("/api/users", json=body, headers=as_admin)
    assert created.status_code == 201 and created.json()["role"] == "staff"
    assert client.post("/api/users", json=body, headers=as_admin).status_code == 409


def test_the_app_refuses_a_short_secret_key():
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="short", _env_file=None)


def test_first_admin_is_seeded_once(session, monkeypatch):
    from app import main

    first_admin = {"ADMIN_EMAIL": "boss@example.com", "ADMIN_PASSWORD": "long-enough-1"}
    settings = Settings(SECRET_KEY="x" * 40, _env_file=None, **first_admin)
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    assert seed_admin(session) is True
    assert seed_admin(session) is False
