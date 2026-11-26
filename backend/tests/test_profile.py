from conftest import PASSWORD
from sqlalchemy import create_engine, text

from app.upgrade import add_missing_columns


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
    assert add_missing_columns(engine) == [
        "users.name",
        "users.username",
        "items.description",
        "items.stock_private",
        "items.history_private",
    ]
    assert add_missing_columns(engine) == []
    with engine.connect() as db:
        assert db.execute(text("SELECT username FROM users")).scalar() == "user7"
