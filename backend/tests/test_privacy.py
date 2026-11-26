import pytest

HIDDEN = {"quantity": None, "reorder_level": None, "low_stock": None}
STOCK = {"quantity": 2, "reorder_level": 5, "low_stock": True}
PNG = b"\x89PNG\r\n\x1a\n"


def stock_of(item):
    return {key: item[key] for key in HIDDEN}


@pytest.fixture
def secret(client, as_admin, as_staff):
    """A low item with one movement, then made private by the admin."""
    body = {"sku": "S-1", "name": "Secret", "quantity": 3, "reorder_level": 5}
    item = client.post("/api/items", json=body, headers=as_admin).json()
    url = f"/api/items/{item['id']}"
    client.post(f"{url}/movements", json={"change": -1}, headers=as_staff)
    assert client.patch(url, json={"stock_private": True}, headers=as_admin).json()["stock_private"] is True
    return url


def test_only_an_admin_switches_between_public_and_private(client, secret, as_staff):
    assert client.patch(secret, json={"stock_private": False}, headers=as_staff).status_code == 403
    assert client.get(secret, headers=as_staff).json()["stock_private"] is True


def test_private_stock_is_hidden_from_staff_wherever_an_item_is_sent(client, secret, as_staff):
    one = client.get(secret, headers=as_staff).json()
    listed = client.get("/api/items", headers=as_staff).json()[0]
    renamed = client.patch(secret, json={"name": "Still secret"}, headers=as_staff).json()
    added = client.post(f"{secret}/images", content=PNG, headers=as_staff).json()
    removed = client.delete(f"{secret}/images/{added['image_ids'][0]}", headers=as_staff).json()
    for item in (one, listed, renamed, added, removed):
        assert stock_of(item) == HIDDEN
        assert (item["sku"], item["stock_private"]) == ("S-1", True)  # SKU and ID are always public
        assert item["id"]


def test_private_stock_cannot_be_worked_out_from_other_endpoints(client, secret, as_staff):
    assert client.get("/api/items?low=true", headers=as_staff).json() == []
    assert client.post(f"{secret}/movements", json={"change": -100}, headers=as_staff).status_code == 403
    assert client.patch(secret, json={"reorder_level": 0}, headers=as_staff).status_code == 403


def test_an_admin_still_sees_and_moves_private_stock(client, secret, as_admin):
    assert stock_of(client.get(secret, headers=as_admin).json()) == STOCK
    assert len(client.get("/api/items?low=true", headers=as_admin).json()) == 1
    assert client.post(f"{secret}/movements", json={"change": 1}, headers=as_admin).json()["quantity"] == 3


def test_making_it_public_again_shows_it(client, secret, as_admin, as_staff):
    client.patch(secret, json={"stock_private": False}, headers=as_admin)
    assert stock_of(client.get(secret, headers=as_staff).json()) == STOCK


def test_history_is_chosen_apart_from_the_stock(client, secret, as_admin, as_staff):
    # private stock, public history: the changes are listed, the totals are not
    assert [m["change"] for m in client.get(f"{secret}/movements", headers=as_staff).json()] == [-1]
    assert len(client.get("/api/movements", headers=as_staff).json()) == 1
    # public stock, private history: the other way round
    client.patch(secret, json={"stock_private": False, "history_private": True}, headers=as_admin)
    assert stock_of(client.get(secret, headers=as_staff).json()) == STOCK
    assert client.get(f"{secret}/movements", headers=as_staff).status_code == 403
    assert client.get("/api/movements", headers=as_staff).json() == []
    assert client.post(f"{secret}/movements", json={"change": 1}, headers=as_staff).status_code == 200
    assert len(client.get(f"{secret}/movements", headers=as_admin).json()) == 2
    assert len(client.get("/api/movements", headers=as_admin).json()) == 2


def test_only_an_admin_switches_the_history(client, secret, as_staff):
    assert client.patch(secret, json={"history_private": True}, headers=as_staff).status_code == 403
