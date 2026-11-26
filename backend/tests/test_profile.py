import pytest
from conftest import PASSWORD
from sqlalchemy import create_engine, text

from app.upgrade import add_missing_columns

ITEM = {"sku": "L-1", "name": "Laptop", "quantity": 1, "reorder_level": 0}


@pytest.fixture
def laptop(client, as_admin):
    created = client.post("/api/items", json=ITEM, headers=as_admin).json()
    client.post(f"/api/items/{created['id']}/detach", headers=as_admin)
    return created


def act(client, headers, item, action):
    return client.post(f"/api/items/{item['id']}/{action}", headers=headers)


def test_attach_shows_the_item_on_my_profile(client, laptop, as_staff, as_admin, staff):
    assert act(client, as_staff, laptop, "attach").json()["owner"]["id"] == staff.id
    assert [i["sku"] for i in client.get("/api/items?mine=true", headers=as_staff).json()] == ["L-1"]
    assert client.get("/api/items?mine=true", headers=as_admin).json() == []


def test_an_attached_item_cannot_be_taken_by_someone_else(client, laptop, as_staff, as_admin):
    act(client, as_admin, laptop, "attach")
    assert act(client, as_staff, laptop, "attach").status_code == 409
    assert act(client, as_staff, laptop, "detach").status_code == 403


def test_owner_or_admin_can_detach(client, laptop, as_staff, as_admin):
    act(client, as_staff, laptop, "attach")
    assert act(client, as_staff, laptop, "detach").json()["owner"] is None
    act(client, as_staff, laptop, "attach")
    assert act(client, as_admin, laptop, "detach").json()["owner"] is None


def test_only_an_admin_assigns_items_to_others(client, laptop, as_staff, as_admin, staff):
    url = f"/api/items/{laptop['id']}/owner"
    assert client.put(url, json={"user_id": staff.id}, headers=as_staff).status_code == 403
    assert client.put(url, json={"user_id": staff.id}, headers=as_admin).json()["owner"]["id"] == staff.id
    assert client.put(url, json={"user_id": 999}, headers=as_admin).status_code == 404
    assert client.put(url, json={"user_id": None}, headers=as_admin).json()["owner"] is None


def test_i_can_edit_my_name_but_not_my_role(client, as_staff):
    response = client.patch("/api/auth/me", json={"name": "  Dana  ", "role": "admin"}, headers=as_staff)
    assert response.json()["name"] == "Dana" and response.json()["role"] == "staff"


def test_changing_the_password(client, staff, as_staff):
    def change(current, new):
        body = {"current_password": current, "new_password": new}
        return client.post("/api/auth/password", json=body, headers=as_staff).status_code

    def login(password):
        return client.post("/api/auth/login", json={"login": staff.email, "password": password}).status_code

    assert change("wrong-password", "another-password") == 400
    assert change(PASSWORD, "short") == 422
    assert change(PASSWORD, "another-password") == 204
    assert login(PASSWORD) == 401 and login("another-password") == 200


def test_only_an_admin_sees_the_user_list(client, as_staff, as_admin, staff):
    assert client.get("/api/users", headers=as_staff).status_code == 403
    users = client.get("/api/users", headers=as_admin).json()
    assert [u["username"] for u in users] == ["admin", "staff"]
    assert "password_hash" not in users[0]


def test_old_databases_gain_the_new_columns_once():
    engine = create_engine("sqlite://")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        db.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY)"))
        db.execute(text("INSERT INTO users (id) VALUES (7)"))
    assert add_missing_columns(engine) == ["users.name", "users.username", "items.owner_id"]
    assert add_missing_columns(engine) == []
    with engine.connect() as db:
        assert db.execute(text("SELECT username FROM users")).scalar() == "user7"
