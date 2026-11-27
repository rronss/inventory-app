import pytest

from app.updates import SYSTEM_UPDATES, seed_updates

NOTICE = {"title": "Stock count", "text": "Friday at 9."}


def listed(client, headers):
    return client.get("/api/updates", headers=headers).json()


def unread(client, headers):
    return client.get("/api/inbox/unread", headers=headers).json()["updates"]


def test_system_updates_are_stored_once(client, session, as_staff):
    assert seed_updates(session) == len(SYSTEM_UPDATES)
    assert seed_updates(session) == 0
    entries = listed(client, as_staff)
    assert {e["kind"] for e in entries} == {"system"} and len(entries) == len(SYSTEM_UPDATES)
    assert len({key for key, *_ in SYSTEM_UPDATES}) == len(SYSTEM_UPDATES)  # keys are unique


def test_an_admin_posts_and_everyone_reads(client, session, as_staff, as_admin):
    seed_updates(session)
    posted = client.post("/api/updates", json=NOTICE, headers=as_admin)
    assert posted.status_code == 201
    newest = listed(client, as_staff)[0]  # dated now, so above the system notes
    seen = (newest["kind"], newest["title"], newest["author"], newest["unread"])
    assert seen == ("admin", "Stock count", "admin", True)
    assert unread(client, as_staff) == len(SYSTEM_UPDATES) + 1


def test_reading_clears_the_number_until_something_new(client, session, as_staff, as_admin):
    seed_updates(session)
    assert client.post("/api/updates/read", headers=as_staff).status_code == 204
    assert unread(client, as_staff) == 0
    client.post("/api/updates", json=NOTICE, headers=as_admin)
    assert unread(client, as_staff) == 1
    assert [e["unread"] for e in listed(client, as_staff)][:2] == [True, False]
    client.post("/api/updates/read", headers=as_staff)
    assert unread(client, as_staff) == 0


def test_only_admins_post_and_remove(client, session, as_staff, as_admin):
    seed_updates(session)
    assert client.post("/api/updates", json=NOTICE, headers=as_staff).status_code == 403
    mine = client.post("/api/updates", json=NOTICE, headers=as_admin).json()["id"]
    assert client.delete(f"/api/updates/{mine}", headers=as_staff).status_code == 403
    system = next(e["id"] for e in listed(client, as_admin) if e["kind"] == "system")
    assert client.delete(f"/api/updates/{system}", headers=as_admin).status_code == 400
    assert client.delete(f"/api/updates/{mine}", headers=as_admin).status_code == 204
    assert client.delete(f"/api/updates/{mine}", headers=as_admin).status_code == 404


@pytest.mark.parametrize(
    "body", [{"title": "", "text": "x"}, {"title": "x", "text": "   "}, {"title": "x" * 121, "text": "x"}]
)
def test_a_message_needs_a_title_and_words(client, as_admin, body):
    assert client.post("/api/updates", json=body, headers=as_admin).status_code == 422


@pytest.mark.parametrize("method, path", [("get", ""), ("post", ""), ("post", "/read"), ("delete", "/1")])
def test_updates_need_a_sign_in(client, method, path):
    assert client.request(method.upper(), f"/api/updates{path}").status_code == 401
