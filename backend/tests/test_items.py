import pytest

WIDGET = {"sku": "W-1", "name": "Widget", "quantity": 10, "reorder_level": 3}


@pytest.fixture
def widget(client, as_admin):
    return client.post("/api/items", json=WIDGET, headers=as_admin).json()


def move(client, headers, item, change, note=""):
    return client.post(f"/api/items/{item['id']}/movements", json={"change": change, "note": note}, headers=headers)


def test_admin_adds_an_item_and_staff_can_see_it(client, widget, as_staff):
    assert widget["quantity"] == 10 and widget["low_stock"] is False
    assert [i["sku"] for i in client.get("/api/items", headers=as_staff).json()] == ["W-1"]


def test_a_new_item_is_attached_to_whoever_adds_it(client, as_staff, staff):
    created = client.post("/api/items", json=WIDGET, headers=as_staff)
    assert created.status_code == 201 and created.json()["owner"]["id"] == staff.id


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
