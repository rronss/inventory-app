import pytest


def ask(client, headers, person):
    return client.post(f"/api/friends/{person.id}", headers=headers)


def state(client, headers, person):
    return client.get(f"/api/friends/{person.id}", headers=headers).json()["status"]


def lists(client, headers):
    found = client.get("/api/friends", headers=headers).json()
    return {key: [p["username"] for p in found[key]] for key in found}


def alerts(client, headers):
    return [(a["kind"], a["person_id"], a["is_read"]) for a in client.get("/api/inbox", headers=headers).json()]


def test_a_request_is_sent_seen_and_accepted(client, staff, admin, as_staff, as_admin):
    assert ask(client, as_staff, admin).json()["status"] == "sent"
    assert state(client, as_admin, staff) == "received"
    assert lists(client, as_admin) == {"friends": [], "incoming": ["staff"], "outgoing": [], "blocked": []}
    assert alerts(client, as_admin) == [("friend_request", staff.id, False)]
    assert client.post(f"/api/friends/{staff.id}/accept", headers=as_admin).json()["status"] == "friends"
    assert lists(client, as_staff)["friends"] == ["admin"]
    assert alerts(client, as_admin) == [("friend_request", staff.id, True)]  # dealt with
    assert alerts(client, as_staff) == [("friend_accepted", admin.id, False)]


def test_only_the_person_asked_can_accept(client, staff, admin, as_staff, as_admin):
    ask(client, as_staff, admin)
    assert client.post(f"/api/friends/{admin.id}/accept", headers=as_staff).status_code == 404
    assert state(client, as_staff, admin) == "sent"


def test_asking_twice_and_asking_back(client, staff, admin, as_staff, as_admin):
    ask(client, as_staff, admin)
    ask(client, as_staff, admin)
    assert len(alerts(client, as_admin)) == 1
    assert ask(client, as_admin, staff).json()["status"] == "friends"  # both asked: friends


@pytest.mark.parametrize("who", ["sender", "receiver"])
def test_a_request_can_be_cancelled_or_declined_and_a_friend_removed(client, staff, admin, as_staff, as_admin, who):
    ask(client, as_staff, admin)
    headers, other = (as_staff, admin) if who == "sender" else (as_admin, staff)
    assert client.delete(f"/api/friends/{other.id}", headers=headers).json()["status"] == "none"
    assert lists(client, as_admin) == {"friends": [], "incoming": [], "outgoing": [], "blocked": []}
    ask(client, as_staff, admin)
    client.post(f"/api/friends/{staff.id}/accept", headers=as_admin)
    client.delete(f"/api/friends/{other.id}", headers=headers)
    assert state(client, as_staff, admin) == "none"


def message(client, headers, person):
    return client.post(f"/api/messages/{person.id}", json={"text": "hi"}, headers=headers).status_code


def test_blocking_ends_the_friendship_and_stops_requests_and_messages(client, staff, admin, as_staff, as_admin):
    ask(client, as_staff, admin)
    client.post(f"/api/friends/{staff.id}/accept", headers=as_admin)
    assert client.put(f"/api/friends/{staff.id}/block", headers=as_admin).json()["status"] == "blocked"
    assert lists(client, as_admin) == {"friends": [], "incoming": [], "outgoing": [], "blocked": ["staff"]}
    assert lists(client, as_staff)["friends"] == [] and lists(client, as_staff)["blocked"] == []
    assert state(client, as_staff, admin) == "none"  # they are not told
    assert state(client, as_admin, staff) == "blocked"
    for headers, other in ((as_staff, admin), (as_admin, staff)):  # in both directions
        assert ask(client, headers, other).status_code == 403
        assert message(client, headers, other) == 403


def test_unblocking_allows_contact_again(client, staff, admin, as_staff, as_admin):
    client.put(f"/api/friends/{staff.id}/block", headers=as_admin)
    client.put(f"/api/friends/{staff.id}/block", headers=as_admin)  # twice is the same as once
    assert client.delete(f"/api/friends/{staff.id}/block", headers=as_admin).json()["status"] == "none"
    assert message(client, as_staff, admin) == 201
    assert ask(client, as_staff, admin).json()["status"] == "sent"


def test_only_the_one_who_blocked_can_unblock(client, staff, admin, as_staff, as_admin):
    client.put(f"/api/friends/{staff.id}/block", headers=as_admin)
    client.delete(f"/api/friends/{admin.id}/block", headers=as_staff)
    assert message(client, as_staff, admin) == 403
    assert client.put(f"/api/friends/{staff.id}/block").status_code == 401


def test_you_cannot_befriend_yourself_or_nobody(client, staff, as_staff):
    assert ask(client, as_staff, staff).status_code == 400
    assert client.post("/api/friends/999", headers=as_staff).status_code == 404


def test_friends_are_private_to_each_person_and_unlock_nothing(client, staff, admin, as_staff, as_admin):
    item = client.post("/api/items", json={"sku": "F-1", "name": "Fan"}, headers=as_admin).json()
    client.patch(f"/api/items/{item['id']}", json={"stock_private": True}, headers=as_admin)
    ask(client, as_staff, admin)
    client.post(f"/api/friends/{staff.id}/accept", headers=as_admin)
    assert client.get(f"/api/items/{item['id']}", headers=as_staff).json()["quantity"] is None
    assert "@example.com" not in client.get("/api/friends", headers=as_staff).text


@pytest.mark.parametrize(
    "method, path", [("get", ""), ("get", "/1"), ("post", "/1"), ("post", "/1/accept"), ("delete", "/1")]
)
def test_friends_need_a_sign_in(client, method, path):
    assert getattr(client, method)(f"/api/friends{path}").status_code == 401
