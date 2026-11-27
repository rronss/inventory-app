import pytest

from app.images import MAX_IMAGE_BYTES, MAX_IMAGES

PNG = b"\x89PNG\r\n\x1a\n" + b"pixels"
WIDGET = {"sku": "W-1", "name": "Widget", "description": "Spare part"}


@pytest.fixture
def widget(client, as_staff):
    return client.post("/api/items", json=WIDGET, headers=as_staff).json()


@pytest.fixture
def other(client):
    body = {"email": "other@example.com", "username": "other", "password": "long-enough-1"}
    token = client.post("/api/auth/register", json=body).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def images_url(item):
    return f"/api/items/{item['id']}/images"


def test_a_new_item_can_have_a_description_and_no_images(widget):
    assert (widget["description"], widget["image_ids"]) == ("Spare part", [])


def test_anyone_signed_in_changes_the_description(client, widget, as_staff, other):
    url = f"/api/items/{widget['id']}"
    assert client.patch(url, json={"description": "  Blue one  "}, headers=as_staff).json()["description"] == "Blue one"
    assert client.patch(url, json={"description": "Green one"}, headers=other).status_code == 200
    assert client.patch(url, json={"description": "x" * 1001}, headers=as_staff).status_code == 422
    assert client.patch(url, json={"description": "no sign-in"}).status_code == 401


def test_editing_the_details(client, widget, as_staff):
    url = f"/api/items/{widget['id']}"
    changes = {"name": "Gadget", "sku": "G-1", "reorder_level": 4}
    edited = client.patch(url, json=changes, headers=as_staff).json()
    assert {key: edited[key] for key in changes} == changes
    assert edited["description"] == "Spare part"  # left out: unchanged
    assert client.patch(url, json={"sku": "G-1"}, headers=as_staff).status_code == 200  # its own SKU
    for bad in ({"name": ""}, {"sku": ""}, {"reorder_level": -1}):
        assert client.patch(url, json=bad, headers=as_staff).status_code == 422


def test_editing_cannot_take_another_sku_or_change_the_quantity(client, widget, as_staff):
    client.post("/api/items", json={**WIDGET, "sku": "W-2"}, headers=as_staff)
    url = f"/api/items/{widget['id']}"
    assert client.patch(url, json={"sku": "W-2"}, headers=as_staff).status_code == 409
    assert client.patch(url, json={"quantity": 99}, headers=as_staff).json()["quantity"] == widget["quantity"]


def test_adding_viewing_and_removing_images(client, widget, as_staff, other):
    url = images_url(widget)
    first = client.post(url, content=PNG, headers=as_staff)
    assert first.status_code == 201
    one = first.json()["image_ids"][0]
    both = client.post(url, content=PNG + b"2", headers=as_staff).json()["image_ids"]
    assert both[0] == one and len(both) == 2  # kept in the order they were added
    shown = client.get(f"{url}/{both[1]}", headers=other)  # anyone signed in may look
    assert shown.content == PNG + b"2" and shown.headers["content-type"] == "image/png"
    assert client.delete(f"{url}/{one}", headers=as_staff).json()["image_ids"] == [both[1]]
    assert client.get(f"{url}/{one}", headers=as_staff).status_code == 404


def test_arranging_images_and_choosing_the_main_one(client, widget, as_staff):
    url = images_url(widget)
    for _ in range(3):
        ids = client.post(url, content=PNG, headers=as_staff).json()["image_ids"]
    new_order = [ids[2], ids[0], ids[1]]
    assert client.put(f"{url}/order", json={"image_ids": new_order}, headers=as_staff).json()["image_ids"] == new_order
    assert client.get(f"/api/items/{widget['id']}", headers=as_staff).json()["image_ids"] == new_order
    added = client.post(url, content=PNG, headers=as_staff).json()["image_ids"]
    assert added[:3] == new_order and len(added) == 4  # a new picture goes to the end
    assert client.delete(f"{url}/{new_order[0]}", headers=as_staff).json()["image_ids"] == added[1:]


def test_an_order_must_list_each_image_once(client, widget, as_staff, staff, session):
    url = images_url(widget)
    first = client.post(url, content=PNG, headers=as_staff).json()["image_ids"][0]
    second = client.post(url, content=PNG, headers=as_staff).json()["image_ids"][1]
    for wrong in ([first], [first, first], [first, second, 999]):
        assert client.put(f"{url}/order", json={"image_ids": wrong}, headers=as_staff).status_code == 422
    assert client.put(f"{url}/order", json={"image_ids": [second, first]}).status_code == 401
    staff.can_edit_items = False
    session.commit()
    assert client.put(f"{url}/order", json={"image_ids": [second, first]}, headers=as_staff).status_code == 403


def test_an_image_is_reached_only_through_its_own_item(client, widget, as_staff):
    second = client.post("/api/items", json={**WIDGET, "sku": "W-2"}, headers=as_staff).json()
    image = client.post(images_url(widget), content=PNG, headers=as_staff).json()["image_ids"][0]
    assert client.get(f"{images_url(second)}/{image}", headers=as_staff).status_code == 404
    assert client.delete(f"{images_url(second)}/{image}", headers=as_staff).status_code == 404


def test_an_item_holds_a_limited_number_of_images(client, widget, as_staff):
    for _ in range(MAX_IMAGES):
        assert client.post(images_url(widget), content=PNG, headers=as_staff).status_code == 201
    assert client.post(images_url(widget), content=PNG, headers=as_staff).status_code == 409


def test_images_need_a_sign_in(client, widget, as_staff):
    url = images_url(widget)
    image = client.post(url, content=PNG, headers=as_staff).json()["image_ids"][0]
    assert client.get(f"{url}/{image}").status_code == 401
    assert client.post(url, content=PNG).status_code == 401
    assert client.delete(f"{url}/{image}").status_code == 401


@pytest.mark.parametrize("data", [b"", b"<svg onload=alert(1)>", b"GIF89a-not-allowed"])
def test_only_png_jpeg_and_webp_are_accepted(client, widget, as_staff, data):
    headers = {**as_staff, "Content-Type": "image/png"}  # the claim is not believed
    assert client.post(images_url(widget), content=data, headers=headers).status_code == 415


def test_a_large_image_is_refused(client, widget, as_staff):
    data = PNG + bytes(MAX_IMAGE_BYTES)
    assert client.post(images_url(widget), content=data, headers=as_staff).status_code == 413
