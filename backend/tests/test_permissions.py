import pytest
from conftest import PASSWORD

ITEM = {"sku": "A-1", "name": "Amp", "quantity": 5, "reorder_level": 1}
PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def item(client, as_admin):
    return client.post("/api/items", json=ITEM, headers=as_admin).json()


def allow(client, headers, person, **changes):
    return client.patch(f"/api/users/{person.id}/permissions", json=changes, headers=headers)


def log_of(client, headers, person, query=""):
    return client.get(f"/api/users/{person.id}/activity{query}", headers=headers)


def test_staff_start_with_every_permission(client, as_staff):
    me = client.get("/api/auth/me", headers=as_staff).json()
    assert (me["can_add_items"], me["can_move_stock"], me["can_edit_items"]) == (True, True, True)


def test_each_switch_is_enforced_by_the_server(client, item, staff, as_staff, as_admin):
    url = f"/api/items/{item['id']}"

    def attempts():
        return (
            client.post("/api/items", json={**ITEM, "sku": "A-2"}, headers=as_staff).status_code,
            client.post(f"{url}/movements", json={"change": 1}, headers=as_staff).status_code,
            client.patch(url, json={"name": "Amp 2"}, headers=as_staff).status_code,
            client.post(f"{url}/images", content=PNG, headers=as_staff).status_code,
        )

    assert attempts() == (201, 200, 200, 201)
    allow(client, as_admin, staff, can_add_items=False, can_move_stock=False, can_edit_items=False)
    assert attempts() == (403, 403, 403, 403)
    image = client.get(url, headers=as_staff).json()["image_ids"][0]
    assert client.delete(f"{url}/images/{image}", headers=as_staff).status_code == 403
    assert client.get(url, headers=as_staff).status_code == 200  # looking is not a permission


def test_admins_are_not_limited_by_the_switches(client, item, admin, as_admin, session):
    admin.can_move_stock = False
    session.commit()
    assert client.post(f"/api/items/{item['id']}/movements", json={"change": 1}, headers=as_admin).status_code == 200


def test_making_someone_an_admin(client, staff, as_staff, as_admin):
    assert client.get("/api/users", headers=as_staff).status_code == 403
    assert allow(client, as_admin, staff, role="admin").json()["role"] == "admin"
    assert client.get("/api/users", headers=as_staff).status_code == 200
    assert allow(client, as_admin, staff, role="owner").status_code == 422


def test_who_may_change_permissions(client, admin, staff, as_staff, as_admin):
    assert allow(client, as_staff, staff, role="admin").status_code == 403
    assert allow(client, as_admin, admin, role="staff").status_code == 400  # so an admin always remains
    assert client.patch("/api/users/999/permissions", json={}, headers=as_admin).status_code == 404
    assert client.get(f"/api/users/{staff.id}", headers=as_admin).json()["role"] == "staff"
    assert client.get(f"/api/users/{staff.id}", headers=as_staff).status_code == 403


def test_the_log_covers_sign_ins_stock_items_and_account_changes(client, item, staff, as_staff, as_admin):
    client.post("/api/auth/login", json={"login": "staff", "password": "not-the-password"})
    client.post("/api/auth/login", json={"login": "staff", "password": PASSWORD})
    url = f"/api/items/{item['id']}"
    client.post(f"{url}/movements", json={"change": -2, "note": "to the lab"}, headers=as_staff)
    client.patch(url, json={"name": "Big amp"}, headers=as_staff)
    client.post("/api/items", json={**ITEM, "sku": "A-2", "name": "Cable"}, headers=as_staff)
    client.post("/api/auth/email", json={"new_email": "n@example.com", "current_password": PASSWORD}, headers=as_staff)
    passwords = {"current_password": PASSWORD, "new_password": "brand-new-pass"}
    client.post("/api/auth/password", json=passwords, headers=as_staff)
    entries = log_of(client, as_admin, staff).json()
    assert [e["action"] for e in entries] == [
        "password_changed", "email_changed", "item_added", "item_edited", "stock_out", "sign_in", "sign_in_failed",
    ]
    assert entries[4]["detail"] == f"-2 Amp (ID {item['id']}): to the lab"
    text = log_of(client, as_admin, staff).text
    assert all(secret not in text for secret in ("@example.com", PASSWORD, "brand-new-pass", "not-the-password"))


def test_the_log_keeps_what_was_removed(client, item, admin, as_admin):
    client.delete(f"/api/items/{item['id']}", headers=as_admin)
    entry = log_of(client, as_admin, admin).json()[0]
    assert (entry["action"], entry["detail"]) == ("item_removed", f"Amp (ID {item['id']}), SKU A-1")


def test_a_permission_change_appears_in_both_logs(client, admin, staff, as_admin):
    allow(client, as_admin, staff, can_move_stock=False)
    allow(client, as_admin, staff, can_move_stock=False)  # nothing changes, nothing is written
    mine, theirs = log_of(client, as_admin, admin).json(), log_of(client, as_admin, staff).json()
    assert [(e["action"], e["detail"]) for e in theirs] == [("permissions_changed", "by admin: stock in/out off")]
    assert [(e["action"], e["detail"]) for e in mine] == [("changed_permissions", "of staff: stock in/out off")]


def test_only_admins_read_logs_a_page_at_a_time(client, item, admin, staff, as_staff, as_admin):
    for _ in range(3):
        client.post(f"/api/items/{item['id']}/movements", json={"change": 1}, headers=as_staff)
    assert log_of(client, as_staff, staff).status_code == 403
    assert client.get(f"/api/users/{staff.id}/activity").status_code == 401
    newest = log_of(client, as_admin, staff, "?limit=2").json()
    older = log_of(client, as_admin, staff, f"?limit=2&before={newest[-1]['id']}").json()
    assert len(newest) == 2 and len(older) == 1
    assert log_of(client, as_admin, staff, "?limit=500").status_code == 422
