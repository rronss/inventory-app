import pytest
from conftest import PASSWORD
from pydantic import ValidationError

from app.config import Settings
from app.main import seed_admin


def test_login_returns_a_token_that_works(client, admin):
    response = client.post("/api/auth/login", json={"login": "ADMIN@example.com", "password": PASSWORD})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "admin"


@pytest.mark.parametrize("email, password", [("admin@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)])
def test_wrong_credentials_get_the_same_answer(client, admin, email, password):
    response = client.post("/api/auth/login", json={"login": email, "password": password})
    assert response.status_code == 401 and response.json()["detail"] == "Wrong sign-in details"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-token"}])
def test_pages_need_a_valid_token(client, headers):
    assert client.get("/api/items", headers=headers).status_code == 401


NEWCOMER = {"name": "Noa", "username": "Noa", "email": "Noa@Example.com", "password": "long-enough-1"}


def test_registering_creates_a_staff_account_and_signs_in(client):
    response = client.post("/api/auth/register", json=NEWCOMER)
    assert response.status_code == 201
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = client.get("/api/auth/me", headers=headers).json()
    assert (me["username"], me["name"], me["role"]) == ("Noa", "Noa", "staff")


def test_nobody_can_register_themselves_as_admin(client):
    token = client.post("/api/auth/register", json={**NEWCOMER, "role": "admin"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "staff"
    assert client.get("/api/users", headers=headers).status_code == 403


@pytest.mark.parametrize("change, status", [({"password": "short"}, 422), ({"email": "not-an-email"}, 422)])
def test_registration_checks_the_input(client, change, status):
    assert client.post("/api/auth/register", json={**NEWCOMER, **change}).status_code == status


def test_an_email_can_register_only_once(client):
    assert client.post("/api/auth/register", json=NEWCOMER).status_code == 201
    assert client.post("/api/auth/register", json=NEWCOMER).status_code == 409


def test_the_admin_user_endpoint_stays_closed(client):
    assert client.post("/api/users", json=NEWCOMER).status_code == 401


def test_only_an_admin_can_add_users(client, as_staff, as_admin):
    body = {"email": "new@example.com", "username": "newbie", "password": "long-enough-1"}
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
