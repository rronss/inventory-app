import pytest

from app.models import ItemImage

WIDGET = {"sku": "W-1", "name": "Widget", "quantity": 10, "reorder_level": 3}


@pytest.fixture
def widget(client, as_admin):
    return client.post("/api/items", json=WIDGET, headers=as_admin).json()


def move(client, headers, item, change, note=""):
    return client.post(f"/api/items/{item['id']}/movements", json={"change": change, "note": note}, headers=headers)


def test_admin_adds_an_item_and_staff_can_see_it(client, widget, as_staff):
    assert widget["quantity"] == 10 and widget["low_stock"] is False
    assert [i["sku"] for i in client.get("/api/items", headers=as_staff).json()] == ["W-1"]


def test_sku_is_unique(client, widget, as_admin):
    assert client.post("/api/items", json=WIDGET, headers=as_admin).status_code == 409


def test_stock_goes_in_and_out(client, widget, as_staff):
    assert move(client, as_staff, widget, 5).json()["quantity"] == 15
    assert move(client, as_staff, widget, -12).json()["quantity"] == 3


def test_stock_cannot_go_below_zero(client, widget, as_staff):
    response = move(client, as_staff, widget, -11)
    assert response.status_code == 409 and response.json()["detail"] == "Not enough stock"
    assert client.get("/api/items", headers=as_staff).json()[0]["quantity"] == 10
    assert client.get(f"/api/items/{widget['id']}/movements", headers=as_staff).json() == []


def test_taking_the_last_unit_is_allowed(client, widget, as_staff):
    assert move(client, as_staff, widget, -10).json()["quantity"] == 0


def test_low_stock_starts_at_the_reorder_level(client, widget, as_staff):
    assert client.get("/api/items?low=true", headers=as_staff).json() == []
    assert move(client, as_staff, widget, -7).json()["low_stock"] is True
    assert [i["sku"] for i in client.get("/api/items?low=true", headers=as_staff).json()] == ["W-1"]


def test_history_records_who_moved_what(client, widget, as_staff, staff):
    move(client, as_staff, widget, -2, "sold")
    move(client, as_staff, widget, 4, "delivery")
    history = client.get(f"/api/items/{widget['id']}/movements", headers=as_staff).json()
    assert [(m["change"], m["note"]) for m in history] == [(4, "delivery"), (-2, "sold")]
    assert {m["user_id"] for m in history} == {staff.id}


@pytest.mark.parametrize("change", [0, 2_000_000])
def test_invalid_changes_are_rejected(client, widget, as_staff, change):
    assert move(client, as_staff, widget, change).status_code == 422


def test_unknown_item(client, as_staff):
    assert move(client, as_staff, {"id": 999}, 1).status_code == 404


def test_each_item_has_its_own_page_data(client, widget, as_staff):
    url = f"/api/items/{widget['id']}"
    assert client.get(url, headers=as_staff).json() == widget
    assert client.get("/api/items/999", headers=as_staff).status_code == 404
    assert client.get(url).status_code == 401


def test_the_history_names_who_moved_the_stock(client, widget, as_staff):
    move(client, as_staff, widget, -2, "sent to the lab")
    entry = client.get(f"/api/items/{widget['id']}/movements", headers=as_staff).json()[0]
    assert (entry["username"], entry["change"], entry["note"]) == ("staff", -2, "sent to the lab")


def test_all_movements_newest_first_across_items(client, widget, as_staff, as_admin):
    gadget = client.post("/api/items", json={**WIDGET, "sku": "G-1", "name": "Gadget"}, headers=as_admin).json()
    move(client, as_staff, widget, 5, "delivery")
    move(client, as_admin, gadget, -2)
    move(client, as_staff, widget, -1)
    rows = client.get("/api/movements", headers=as_staff).json()
    assert [(r["item_name"], r["change"], r["username"]) for r in rows] == [
        ("Widget", -1, "staff"),
        ("Gadget", -2, "admin"),
        ("Widget", 5, "staff"),
    ]
    assert rows[1]["item_id"] == gadget["id"]
    newest = client.get("/api/movements?limit=2", headers=as_staff).json()
    older = client.get(f"/api/movements?limit=2&before={newest[-1]['id']}", headers=as_staff).json()
    assert [r["change"] for r in newest + older] == [-1, -2, 5]


def test_the_movement_list_needs_a_sign_in_and_a_sane_limit(client, as_staff):
    assert client.get("/api/movements").status_code == 401
    assert client.get("/api/movements?limit=1000", headers=as_staff).status_code == 422


def test_removing_an_item_takes_its_pictures_and_movements_only(client, session, widget, as_staff, as_admin):
    other = client.post("/api/items", json={**WIDGET, "sku": "G-1"}, headers=as_staff).json()
    for item in (widget, other):
        move(client, as_staff, item, 1)
        client.post(f"/api/items/{item['id']}/images", content=b"\x89PNG\r\n\x1a\n", headers=as_staff)
    url = f"/api/items/{widget['id']}"
    assert client.delete(url, headers=as_admin).status_code == 204
    assert client.get(url, headers=as_admin).status_code == 404
    assert [m["item_id"] for m in client.get("/api/movements", headers=as_admin).json()] == [other["id"]]
    assert [image.item_id for image in session.query(ItemImage)] == [other["id"]]
    assert client.delete(url, headers=as_admin).status_code == 404


def test_only_an_admin_removes_items(client, widget, as_staff):
    url = f"/api/items/{widget['id']}"
    assert client.delete(url).status_code == 401
    assert client.delete(url, headers=as_staff).status_code == 403
    assert client.get(url, headers=as_staff).status_code == 200

