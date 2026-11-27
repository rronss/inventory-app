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


def test_changing_the_email(client, staff, admin, as_staff):
    def change(email, password=PASSWORD):
        body = {"new_email": email, "current_password": password}
        return client.post("/api/auth/email", json=body, headers=as_staff)

    def sign_in(login):
        return client.post("/api/auth/login", json={"login": login, "password": PASSWORD}).status_code

    assert change("new@example.com", "wrong-password").status_code == 400
    assert change("not-an-email").status_code == 422
    assert change("ADMIN@example.com").status_code == 409  # someone else's
    assert change("staff@example.com").status_code == 204  # my own, unchanged
    response = change("New@Example.com")
    assert response.status_code == 204 and response.content == b""
    assert sign_in("new@example.com") == 200 and sign_in("staff@example.com") == 401
    anonymous = {"new_email": "x@example.com", "current_password": PASSWORD}
    assert client.post("/api/auth/email", json=anonymous).status_code == 401


def test_my_bio_is_saved_and_the_rest_left_alone(client, as_staff):
    def save(body):
        return client.patch("/api/auth/me", json=body, headers=as_staff)

    save({"name": "Dana"})
    assert save({"bio": "  Stock room, mornings.  "}).json() == save({}).json()
    me = client.get("/api/auth/me", headers=as_staff).json()
    assert (me["bio"], me["name"], me["username"]) == ("Stock room, mornings.", "Dana", "staff")
    assert save({"bio": "x" * 501}).status_code == 422


def test_my_photo_can_be_added_seen_and_removed(client, as_staff, as_admin):
    png = b"\x89PNG\r\n\x1a\n" + b"face"
    assert client.get("/api/auth/photo", headers=as_staff).status_code == 404
    assert client.put("/api/auth/photo", content=png, headers=as_staff).json()["photo_version"] == 1
    assert client.get("/api/auth/photo", headers=as_staff).content == png
    assert client.get("/api/auth/photo", headers=as_admin).status_code == 404  # this address is your own photo
    assert client.delete("/api/auth/photo", headers=as_staff).json()["photo_version"] == 0
    assert client.get("/api/auth/photo", headers=as_staff).status_code == 404


def test_a_photo_must_be_a_small_real_image_from_a_signed_in_user(client, as_staff):
    assert client.put("/api/auth/photo", content=b"<svg>", headers=as_staff).status_code == 415
    large = b"\x89PNG\r\n\x1a\n" + bytes(2 * 1024 * 1024)
    assert client.put("/api/auth/photo", content=large, headers=as_staff).status_code == 413
    assert client.put("/api/auth/photo", content=b"x").status_code == 401
    assert client.get("/api/auth/photo").status_code == 401


def test_only_an_admin_sees_the_user_list(client, as_staff, as_admin, staff):
    assert client.get("/api/users", headers=as_staff).status_code == 403
    users = client.get("/api/users", headers=as_admin).json()
    assert [u["username"] for u in users] == ["admin", "staff"]
    assert "password_hash" not in users[0]


def test_old_databases_gain_the_new_columns_once():
    engine = create_engine("sqlite://")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, role VARCHAR(20))"))
        db.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY)"))
        db.execute(text("CREATE TABLE item_images (id INTEGER PRIMARY KEY)"))
        db.execute(text("CREATE TABLE user_photos (user_id INTEGER PRIMARY KEY)"))
        db.execute(text("INSERT INTO users (id) VALUES (7)"))
    assert add_missing_columns(engine) == [
        "users.name",
        "users.username",
        "users.bio",
        "users.photo_version",
        "users.can_add_items",
        "users.can_move_stock",
        "users.can_edit_items",
        "users.chat_from",
        "items.description",
        "items.stock_private",
        "items.history_private",
        "items.creator_id",
        "items.created_at",
        "item_images.position",
        "item_images.s3_key",
        "user_photos.s3_key",
    ]
    assert add_missing_columns(engine) == []
    with engine.connect() as db:
        assert db.execute(text("SELECT username FROM users")).scalar() == "user7"
