import pytest

ITEM = {"sku": "N-1", "name": "Cable", "quantity": 10, "reorder_level": 5}


@pytest.fixture
def mine(client, as_staff):
    """An item staff added, so its alerts go to staff."""
    return client.post("/api/items", json=ITEM, headers=as_staff).json()


def move(client, headers, item, change):
    return client.post(f"/api/items/{item['id']}/movements", json={"change": change}, headers=headers)


def inbox(client, headers):
    return client.get("/api/inbox", headers=headers).json()


def texts(client, headers):
    return [alert["text"] for alert in inbox(client, headers)]


def unread(client, headers):
    return client.get("/api/inbox/unread", headers=headers).json()["unread"]


def test_low_and_out_of_stock_alert_once_on_the_way_down(client, mine, as_staff):
    move(client, as_staff, mine, -4)  # 6: still fine
    assert inbox(client, as_staff) == []
    move(client, as_staff, mine, -1)  # 5: low
    move(client, as_staff, mine, -2)  # 3: still low, no second alert
    move(client, as_staff, mine, -3)  # 0: out
    name = f"Cable (ID {mine['id']})"
    assert texts(client, as_staff) == [f"{name} is out of stock", f"{name} is low: 5 left"]


def test_someone_elses_stock_change_and_edit_are_reported(client, mine, as_staff, as_admin):
    move(client, as_admin, mine, 3)
    move(client, as_admin, mine, -1)
    client.patch(f"/api/items/{mine['id']}", json={"name": "Long cable"}, headers=as_admin)
    client.post(f"/api/items/{mine['id']}/images", content=b"\x89PNG\r\n\x1a\n", headers=as_admin)
    name = f"(ID {mine['id']})"
    assert texts(client, as_staff) == [
        f"admin edited Long cable {name}: pictures",
        f"admin edited Long cable {name}: name",
        f"admin took 1 from Cable {name}",
        f"admin added 3 to Cable {name}",
    ]
    assert inbox(client, as_admin) == []  # nobody is told about their own doing


def test_your_own_changes_do_not_alert_you(client, mine, as_staff):
    move(client, as_staff, mine, 1)
    client.patch(f"/api/items/{mine['id']}", json={"name": "Mine"}, headers=as_staff)
    assert inbox(client, as_staff) == []


def test_removal_and_permission_changes_arrive(client, mine, staff, as_staff, as_admin):
    client.patch(f"/api/users/{staff.id}/permissions", json={"can_move_stock": False}, headers=as_admin)
    client.delete(f"/api/items/{mine['id']}", headers=as_admin)
    alerts = inbox(client, as_staff)
    assert [(a["kind"], a["item_id"]) for a in alerts] == [("item_removed", None), ("permissions_changed", None)]
    assert alerts[1]["text"] == "admin changed your permissions: stock in/out off"


@pytest.mark.parametrize(
    "setting, expected",
    [("stock_private", ["stock_changed"]), ("history_private", ["low_stock"])],
)
def test_alerts_never_tell_what_is_private(client, mine, as_staff, as_admin, setting, expected):
    client.patch(f"/api/items/{mine['id']}", json={setting: True}, headers=as_admin)
    client.post("/api/inbox/read", headers=as_staff)
    move(client, as_admin, mine, -6)  # makes it low
    assert [a["kind"] for a in inbox(client, as_staff) if not a["is_read"]] == expected


def test_reading_alerts(client, mine, as_staff, as_admin):
    move(client, as_admin, mine, 1)
    move(client, as_admin, mine, 1)
    assert unread(client, as_staff) == 2
    first = inbox(client, as_staff)[0]["id"]
    assert client.post(f"/api/inbox/{first}/read", headers=as_admin).status_code == 404  # not yours
    assert client.post(f"/api/inbox/{first}/read", headers=as_staff).status_code == 204
    assert unread(client, as_staff) == 1
    assert client.post("/api/inbox/read", headers=as_staff).status_code == 204
    assert unread(client, as_staff) == 0


@pytest.mark.parametrize("method, path", [("get", ""), ("get", "/unread"), ("post", "/read"), ("post", "/1/read")])
def test_the_inbox_needs_a_sign_in(client, method, path):
    assert getattr(client, method)(f"/api/inbox{path}").status_code == 401
