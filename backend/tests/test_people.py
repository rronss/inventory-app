import pytest
from sqlalchemy import create_engine, text

from app.upgrade import add_missing_columns

ITEM = {"sku": "P-1", "name": "Printer", "quantity": 2, "reorder_level": 5}


@pytest.fixture
def added(client, as_staff):
    return client.post("/api/items", json=ITEM, headers=as_staff).json()


def get(client, headers, path):
    return client.get(f"/api/people{path}", headers=headers)


def test_a_record_lists_the_items_that_person_added(client, added, staff, admin, as_admin, as_staff):
    client.post("/api/items", json={**ITEM, "sku": "P-2"}, headers=as_admin)
    assert [i["sku"] for i in get(client, as_admin, f"/{staff.id}/items").json()] == ["P-1"]
    assert [i["sku"] for i in get(client, as_staff, f"/{admin.id}/items").json()] == ["P-2"]


def test_private_stock_stays_hidden_in_someone_elses_list(client, added, admin, as_admin, as_staff):
    other = client.post("/api/items", json={**ITEM, "sku": "P-2"}, headers=as_admin).json()
    client.patch(f"/api/items/{other['id']}", json={"stock_private": True}, headers=as_admin)
    assert get(client, as_staff, f"/{admin.id}/items").json()[0]["quantity"] is None
    assert get(client, as_admin, f"/{admin.id}/items").json()[0]["quantity"] == 2


def test_colleagues_see_who_someone_is_but_never_an_email(client, added, staff, as_staff, as_admin):
    png = b"\x89PNG\r\n\x1a\nface"
    client.patch("/api/auth/me", json={"name": "Dana", "bio": "Mornings"}, headers=as_staff)
    client.put("/api/auth/photo", content=png, headers=as_staff)
    record = get(client, as_admin, f"/{staff.id}").json()
    expected = {"id": staff.id, "username": "staff", "name": "Dana", "role": "staff", "bio": "Mornings"}
    assert record == {**expected, "photo_version": 1, "friends": 0}
    assert get(client, as_admin, f"/{staff.id}/photo").content == png
    assert "@example.com" not in get(client, as_admin, f"/{staff.id}/items").text


def test_explore_shows_every_public_item_newest_first(client, added, staff, admin, as_staff, as_admin):
    client.post("/api/items", json={**ITEM, "sku": "E-1"}, headers=as_admin)
    seen = client.get("/api/explore", headers=as_staff).json()
    expected = [("E-1", "admin", admin.id), ("P-1", "staff", staff.id)]  # other people's and your own
    assert [(i["sku"], i["added_by"], i["added_by_id"]) for i in seen] == expected


def test_explore_says_when_each_item_was_added_and_shows_the_adders_photo(client, added, staff, session, as_staff):
    client.put("/api/auth/photo", content=b"\x89PNG\r\n\x1a\nface", headers=as_staff)
    item = client.get("/api/explore", headers=as_staff).json()[0]
    assert item["created_at"] and item["added_by_photo_version"] == 1
    session.execute(text("UPDATE items SET created_at = NULL"))  # as an item from before dates were kept
    session.commit()
    session.expire_all()
    assert client.get("/api/explore", headers=as_staff).json()[0]["created_at"] is None


def test_explore_includes_items_nobody_is_recorded_for(client, added, session, as_staff):
    session.execute(text("UPDATE items SET creator_id = NULL"))
    session.commit()
    session.expire_all()
    item = client.get("/api/explore", headers=as_staff).json()[0]
    assert (item["sku"], item["added_by"], item["added_by_id"]) == ("P-1", None, None)


def test_explore_leaves_out_private_items_for_everyone(client, added, as_admin, as_staff):
    client.patch(f"/api/items/{added['id']}", json={"stock_private": True}, headers=as_admin)
    for headers in (as_staff, as_admin):
        assert client.get("/api/explore", headers=headers).json() == []
    client.patch(f"/api/items/{added['id']}", json={"stock_private": False}, headers=as_admin)
    response = client.get("/api/explore", headers=as_staff)
    assert [i["sku"] for i in response.json()] == ["P-1"] and "@example.com" not in response.text
    assert client.get("/api/explore").status_code == 401


def test_a_record_counts_friends_without_naming_them(client, staff, admin, as_staff, as_admin):
    client.post(f"/api/friends/{admin.id}", headers=as_staff)
    assert get(client, as_staff, f"/{admin.id}").json()["friends"] == 0  # a request is not a friendship
    client.post(f"/api/friends/{staff.id}/accept", headers=as_admin)
    for person in (staff, admin):
        record = get(client, as_staff, f"/{person.id}").json()
        assert record["friends"] == 1 and isinstance(record["friends"], int)


def test_an_unknown_person(client, as_staff):
    for path in ("/999", "/999/photo", "/999/items"):
        assert get(client, as_staff, path).status_code == 404


@pytest.mark.parametrize("path", ["/1", "/1/photo", "/1/items"])
def test_records_need_a_sign_in(client, path):
    assert client.get(f"/api/people{path}").status_code == 401


def test_items_from_before_creators_go_to_the_first_admin():
    engine = create_engine("sqlite://")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, role VARCHAR(20))"))
        db.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY)"))
        db.execute(text("INSERT INTO users (id, role) VALUES (1, 'staff'), (2, 'admin'), (3, 'admin')"))
        db.execute(text("INSERT INTO items (id) VALUES (1)"))
    assert "items.creator_id" in add_missing_columns(engine)
    with engine.connect() as db:
        assert db.execute(text("SELECT creator_id FROM items")).scalar() == 2
