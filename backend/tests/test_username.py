import pytest

ACCOUNT = {"email": "ron@example.com", "password": "long-enough-1", "username": "Ron"}


def register(client, **change):
    return client.post("/api/auth/register", json={**ACCOUNT, **change})


def sign_in(client, login):
    return client.post("/api/auth/login", json={"login": login, "password": ACCOUNT["password"]}).status_code


def headers_of(response):
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize("login", ["Ron", "ron", "RON@example.com"])
def test_sign_in_with_username_or_email(client, login):
    register(client)
    assert sign_in(client, login) == 200


def test_the_username_is_kept_as_typed(client):
    me = client.get("/api/auth/me", headers=headers_of(register(client))).json()
    assert me["username"] == "Ron"


def test_registration_needs_a_username(client):
    without = {key: value for key, value in ACCOUNT.items() if key != "username"}
    assert client.post("/api/auth/register", json=without).status_code == 422


@pytest.mark.parametrize("username", [None, "", "   ", "ab", "a" * 31, "has space", "ron@example.com", "-ron"])
def test_unusable_usernames_are_refused(client, username):
    assert register(client, username=username).status_code == 422


def test_a_username_belongs_to_one_account_whatever_its_case(client, as_staff):
    register(client)
    assert register(client, email="other@example.com", username="rON").status_code == 409
    assert client.patch("/api/auth/me", json={"name": "", "username": "ron"}, headers=as_staff).status_code == 409


def test_changing_or_keeping_the_username(client, as_staff):
    def save(body):
        return client.patch("/api/auth/me", json=body, headers=as_staff)

    assert save({"name": "Dana", "username": "dana"}).json()["username"] == "dana"
    assert save({"name": "Dana", "username": "Dana"}).json()["username"] == "Dana"  # my own, new capitals
    assert save({"name": "Dana B"}).json()["username"] == "Dana"  # left out: unchanged
    assert save({"name": "Dana", "username": ""}).status_code == 422  # cannot be removed


def test_nobody_is_shown_an_email_address(client, as_admin, as_staff):
    register(client)
    client.post("/api/items", json={"sku": "E-1", "name": "Pen"}, headers=as_staff)
    for url, headers in [("/api/auth/me", as_staff), ("/api/users", as_admin), ("/api/items", as_admin)]:
        response = client.get(url, headers=headers)
        assert response.status_code == 200 and "@example.com" not in response.text
