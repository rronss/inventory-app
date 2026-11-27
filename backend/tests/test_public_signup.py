"""Anyone can register, so: attempt limits, a bot check, and new accounts that change only their own items."""
import io
import json

import pytest
from conftest import PASSWORD
from pydantic import ValidationError

from app import botcheck, ratelimit
from app.config import Settings
from app.ratelimit import limiter

ITEM = {"sku": "A-1", "name": "Amp", "quantity": 5, "reorder_level": 1}
PNG = b"\x89PNG\r\n\x1a\n"
NEWCOMER = {"username": "visitor", "email": "visitor@example.com", "password": "long-enough-1"}


def settings(**values) -> Settings:
    return Settings(SECRET_KEY="x" * 40, _env_file=None, **values)


def register(client, headers=None, **changes):
    return client.post("/api/auth/register", json={**NEWCOMER, **changes}, headers=headers or {})


def sign_in(client, login, password=PASSWORD, headers=None):
    return client.post("/api/auth/login", json={"login": login, "password": password}, headers=headers or {})


def bearer(response):
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def theirs(client, as_admin):
    """An item the newcomer did not add."""
    item = client.post("/api/items", json=ITEM, headers=as_admin).json()
    return client.post(f"/api/items/{item['id']}/images", content=PNG, headers=as_admin).json()


# --- what a new account may change ------------------------------------------------------------------------


def test_a_registered_account_is_limited_to_its_own_items(client):
    me = client.get("/api/auth/me", headers=bearer(register(client))).json()
    assert me["own_items_only"] is True and me["role"] == "staff"


def test_it_can_look_at_but_not_change_other_peoples_items(client, theirs):
    them = bearer(register(client))
    url, image = f"/api/items/{theirs['id']}", theirs["image_ids"][0]
    assert client.get(url, headers=them).json()["creator_id"] == theirs["creator_id"]
    refused = [
        client.post(f"{url}/movements", json={"change": -1}, headers=them),
        client.patch(url, json={"name": "Mine now"}, headers=them),
        client.post(f"{url}/images", content=PNG, headers=them),
        client.put(f"{url}/images/order", json={"image_ids": [image]}, headers=them),
        client.delete(f"{url}/images/{image}", headers=them),
    ]
    assert [r.status_code for r in refused] == [403] * 5
    assert "only the items you added" in refused[0].json()["detail"]
    after = client.get(url, headers=them).json()
    assert (after["name"], after["quantity"], after["image_ids"]) == ("Amp", 5, [image])


def test_it_manages_the_items_it_adds(client):
    them = bearer(register(client))
    item = client.post("/api/items", json={**ITEM, "sku": "N-1"}, headers=them).json()
    url = f"/api/items/{item['id']}"
    assert client.post(f"{url}/movements", json={"change": 2}, headers=them).status_code == 200
    assert client.patch(url, json={"name": "My amp"}, headers=them).status_code == 200
    added = client.post(f"{url}/images", content=PNG, headers=them)
    assert added.status_code == 201
    assert client.delete(f"{url}/images/{added.json()['image_ids'][0]}", headers=them).status_code == 200


def test_an_admin_can_lift_the_limit(client, theirs, as_admin):
    response = register(client)
    them = bearer(response)
    my_id = client.get("/api/auth/me", headers=them).json()["id"]
    url = f"/api/users/{my_id}/permissions"
    assert client.patch(url, json={"own_items_only": False}, headers=them).status_code == 403
    assert client.patch(url, json={"own_items_only": False}, headers=as_admin).json()["own_items_only"] is False
    move = client.post(f"/api/items/{theirs['id']}/movements", json={"change": -1}, headers=them)
    assert move.status_code == 200


def test_accounts_an_admin_creates_are_not_limited(client, theirs, as_admin, as_staff):
    created = client.post("/api/users", json=NEWCOMER, headers=as_admin).json()
    assert created["own_items_only"] is False
    move = client.post(f"/api/items/{theirs['id']}/movements", json={"change": 1}, headers=as_staff)
    assert move.status_code == 200


# --- attempt limits ----------------------------------------------------------------------------------------


def test_five_wrong_passwords_lock_that_sign_in_for_a_while(client, staff, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(limiter, "clock", lambda: now[0])
    assert [sign_in(client, staff.email, "wrong-password").status_code for _ in range(5)] == [401] * 5
    refused = sign_in(client, staff.email)  # even with the right password
    assert refused.status_code == 429 and "15 minutes" in refused.json()["detail"]
    assert refused.headers["retry-after"] == "900"
    assert sign_in(client, staff.username).status_code == 429  # the same account by its other name
    now[0] += 901
    assert sign_in(client, staff.email).status_code == 200


def test_signing_in_correctly_clears_the_count(client, staff):
    for _ in range(3):
        for _ in range(4):
            sign_in(client, staff.email, "wrong-password")
        assert sign_in(client, staff.email).status_code == 200


def test_one_address_cannot_try_many_names(client, admin, monkeypatch):
    monkeypatch.setattr(ratelimit, "get_settings", lambda: settings(TRUSTED_PROXIES=1))
    attacker, other = {"X-Forwarded-For": "203.0.113.5"}, {"X-Forwarded-For": "198.51.100.7"}
    codes = [sign_in(client, f"guess{n}@example.com", "x" * 8, attacker).status_code for n in range(21)]
    assert codes == [401] * 20 + [429]
    assert sign_in(client, "admin", headers=other).status_code == 200  # others are not locked out


def test_a_visitor_cannot_pick_their_own_address(client, monkeypatch):
    monkeypatch.setattr(ratelimit, "get_settings", lambda: settings(TRUSTED_PROXIES=2))
    codes = []
    for n in range(21):  # a different made-up first entry each time; our two proxies add the last two
        forged = {"X-Forwarded-For": f"10.9.9.{n}, 203.0.113.5, 172.18.0.2"}
        codes.append(sign_in(client, f"guess{n}@example.com", "x" * 8, forged).status_code)
    assert codes[-1] == 429


def test_one_address_can_only_register_so_often(client):
    codes = [register(client, username=f"u{n:03}", email=f"u{n}@example.com").status_code for n in range(11)]
    assert codes == [201] * 10 + [429]


# --- bot check ---------------------------------------------------------------------------------------------


@pytest.fixture
def turnstile(monkeypatch):
    """The check switched on, with Cloudflare's answer decided here: nothing leaves the machine."""
    asked = []

    def answer(url, body, timeout):
        asked.append((url, body.decode()))
        return io.BytesIO(json.dumps({"success": "response=good-token" in body.decode()}).encode())

    on = settings(TURNSTILE_SITE_KEY="site", TURNSTILE_SECRET_KEY="secret")
    monkeypatch.setattr(botcheck, "get_settings", lambda: on)
    monkeypatch.setattr(botcheck.urllib.request, "urlopen", answer)
    return asked


def test_the_check_is_off_without_keys(client):
    assert client.get("/api/auth/config").json() == {"turnstile_site_key": ""}
    assert register(client).status_code == 201


def test_registration_needs_a_passed_check_when_on(client, turnstile):
    assert register(client).status_code == 400
    assert register(client, turnstile_token="bad-token").status_code == 400
    assert register(client, turnstile_token="good-token").status_code == 201
    url, body = turnstile[-1]
    assert url == botcheck.VERIFY_URL and "secret=secret" in body


def test_if_the_check_cannot_be_reached_nobody_is_registered(client, turnstile, monkeypatch):
    def down(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(botcheck.urllib.request, "urlopen", down)
    assert register(client, turnstile_token="good-token").status_code == 503
    assert sign_in(client, NEWCOMER["email"], NEWCOMER["password"]).status_code == 401


def test_the_two_keys_go_together():
    for values in ({"TURNSTILE_SITE_KEY": "a"}, {"TURNSTILE_SECRET_KEY": "b"}):
        with pytest.raises(ValidationError):
            settings(**{"TURNSTILE_SITE_KEY": "", "TURNSTILE_SECRET_KEY": "", **values})
