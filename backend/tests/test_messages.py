import pytest


def send(client, headers, to, text):
    return client.post(f"/api/messages/{to.id}", json={"text": text}, headers=headers)


def chat(client, headers, other):
    return client.get(f"/api/messages/{other.id}", headers=headers).json()


def waiting(client, headers):
    return client.get("/api/inbox/unread", headers=headers).json()["messages"]


@pytest.fixture
def third(client):
    body = {"email": "third@example.com", "username": "third", "password": "long-enough-1"}
    token = client.post("/api/auth/register", json=body).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_both_sides_see_the_conversation_in_order(client, staff, admin, as_staff, as_admin):
    assert send(client, as_staff, admin, "  Printer is out  ").status_code == 201
    send(client, as_admin, staff, "Ordering one")
    mine = chat(client, as_staff, admin)
    assert [(m["text"], m["mine"]) for m in mine] == [("Printer is out", True), ("Ordering one", False)]
    assert [m["mine"] for m in chat(client, as_admin, staff)] == [False, True]


def test_unread_messages_are_counted_until_read(client, staff, admin, as_staff, as_admin):
    send(client, as_staff, admin, "one")
    send(client, as_staff, admin, "two")
    assert (waiting(client, as_admin), waiting(client, as_staff)) == (2, 0)
    assert client.post(f"/api/messages/{staff.id}/read", headers=as_admin).status_code == 204
    assert waiting(client, as_admin) == 0


def test_the_list_of_conversations(client, staff, admin, as_staff, as_admin, third):
    send(client, as_staff, admin, "hello")
    me = client.get("/api/auth/me", headers=third).json()
    client.post(f"/api/messages/{admin.id}", json={"text": "from third"}, headers=third)
    rows = client.get("/api/messages", headers=as_admin).json()
    assert [(r["person"]["username"], r["last_text"], r["unread"]) for r in rows] == [
        ("third", "from third", 1),
        ("staff", "hello", 1),
    ]
    assert rows[0]["person"]["id"] == me["id"]
    assert "@example.com" not in client.get("/api/messages", headers=as_admin).text


def test_nobody_else_can_read_it_admins_included(client, staff, admin, as_staff, as_admin, third):
    other = client.get("/api/auth/me", headers=third).json()
    client.post(f"/api/messages/{staff.id}", json={"text": "between us"}, headers=third)
    assert client.get("/api/messages", headers=as_admin).json() == []
    assert client.get(f"/api/messages/{staff.id}", headers=as_admin).json() == []
    assert client.get(f"/api/messages/{other['id']}", headers=as_admin).json() == []
    assert "between us" not in client.get(f"/api/users/{staff.id}/activity", headers=as_admin).text


def choose(client, headers, who):
    return client.patch("/api/auth/me", json={"chat_from": who}, headers=headers)


def test_everyone_can_chat_by_default(client, as_staff, admin):
    assert client.get("/api/auth/me", headers=as_staff).json()["chat_from"] == "everyone"
    assert send(client, as_staff, admin, "hi").status_code == 201


def test_friends_only_refuses_others_but_not_friends(client, staff, admin, as_staff, as_admin):
    assert choose(client, as_admin, "friends").json()["chat_from"] == "friends"
    refused = send(client, as_staff, admin, "hi")
    assert refused.status_code == 403 and "only accepts messages from friends" in refused.json()["detail"]
    assert send(client, as_admin, staff, "I can still write to you").status_code == 201
    client.post(f"/api/friends/{admin.id}", headers=as_staff)
    assert send(client, as_staff, admin, "still only a request").status_code == 403
    client.post(f"/api/friends/{staff.id}/accept", headers=as_admin)
    assert send(client, as_staff, admin, "now friends").status_code == 201
    choose(client, as_admin, "everyone")
    client.delete(f"/api/friends/{staff.id}", headers=as_admin)
    assert send(client, as_staff, admin, "open again").status_code == 201


def test_the_chat_setting_is_checked_and_not_shown_to_others(client, as_staff, as_admin, staff):
    assert choose(client, as_staff, "nobody").status_code == 422
    assert "chat_from" not in client.get(f"/api/people/{staff.id}", headers=as_admin).json()


def test_what_cannot_be_sent(client, staff, admin, as_staff):
    assert send(client, as_staff, staff, "me").status_code == 400
    assert client.post("/api/messages/999", json={"text": "x"}, headers=as_staff).status_code == 404
    for text in ("", "   ", "x" * 1001):
        assert send(client, as_staff, admin, text).status_code == 422


@pytest.mark.parametrize("method, path", [("get", ""), ("get", "/1"), ("post", "/1"), ("post", "/1/read")])
def test_messages_need_a_sign_in(client, method, path):
    assert getattr(client, method)(f"/api/messages{path}").status_code == 401


def test_anyone_signed_in_can_list_people_to_write_to(client, staff, admin, as_staff):
    people = client.get("/api/people", headers=as_staff).json()
    assert [p["username"] for p in people] == ["admin", "staff"]
    assert "@example.com" not in client.get("/api/people", headers=as_staff).text
    assert client.get("/api/people").status_code == 401
