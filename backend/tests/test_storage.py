"""Pictures kept in S3, against moto's offline stand-in: nothing here reaches AWS."""
import boto3
import pytest
from moto import mock_aws
from pydantic import ValidationError

from app import storage
from app.config import Settings
from app.models import ItemImage, UserPhoto

ITEM = {"sku": "A-1", "name": "Amp", "quantity": 5, "reorder_level": 1}
PNG = b"\x89PNG\r\n\x1a\n"
BUCKET = "test-pictures"


def settings(**values) -> Settings:
    return Settings(SECRET_KEY="x" * 40, _env_file=None, **values)


@pytest.fixture
def s3(monkeypatch):
    """The app set to keep pictures in a simulated bucket."""
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")  # never the real credentials of whoever runs the tests
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        storage.s3_client.cache_clear()
        client = boto3.client("s3")
        client.create_bucket(Bucket=BUCKET)
        monkeypatch.setattr(storage, "get_settings", lambda: settings(PICTURE_STORAGE="s3", PICTURE_BUCKET=BUCKET))
        yield client
    storage.s3_client.cache_clear()


def files(client) -> list[str]:
    return [entry["Key"] for entry in client.list_objects_v2(Bucket=BUCKET).get("Contents", [])]


@pytest.fixture
def item(client, as_admin):
    return client.post("/api/items", json=ITEM, headers=as_admin).json()


def add_picture(client, headers, item, data=PNG):
    return client.post(f"/api/items/{item['id']}/images", content=data, headers=headers)


def test_an_item_picture_goes_to_s3_and_comes_back(client, s3, item, session, as_admin, as_staff):
    image_id = add_picture(client, as_admin, item, PNG + b"one").json()["image_ids"][0]
    row = session.get(ItemImage, image_id)
    assert files(s3) == [row.s3_key] and row.s3_key.startswith(f"items/{item['id']}/")
    assert row.data == b""  # the database holds only the name
    shown = client.get(f"/api/items/{item['id']}/images/{image_id}", headers=as_staff)
    assert shown.content == PNG + b"one" and shown.headers["content-type"] == "image/png"
    assert client.get(f"/api/items/{item['id']}/images/{image_id}").status_code == 401


def test_removing_a_picture_removes_its_file(client, s3, item, as_admin):
    add_picture(client, as_admin, item)
    first = add_picture(client, as_admin, item).json()["image_ids"][0]
    assert len(files(s3)) == 2
    client.delete(f"/api/items/{item['id']}/images/{first}", headers=as_admin)
    assert len(files(s3)) == 1


def test_removing_an_item_removes_its_files(client, s3, item, as_admin):
    add_picture(client, as_admin, item)
    add_picture(client, as_admin, item)
    assert client.delete(f"/api/items/{item['id']}", headers=as_admin).status_code == 204
    assert files(s3) == []


def test_a_new_profile_photo_replaces_the_old_file(client, s3, staff, session, as_staff, as_admin):
    client.put("/api/auth/photo", content=PNG + b"old", headers=as_staff)
    old = files(s3)
    client.put("/api/auth/photo", content=PNG + b"new", headers=as_staff)
    assert len(files(s3)) == 1 and files(s3) != old and files(s3)[0].startswith(f"people/{staff.id}/")
    assert client.get("/api/auth/photo", headers=as_staff).content == PNG + b"new"
    assert client.get(f"/api/people/{staff.id}/photo", headers=as_admin).content == PNG + b"new"
    client.delete("/api/auth/photo", headers=as_staff)
    assert files(s3) == [] and session.get(UserPhoto, staff.id) is None


def test_pictures_saved_in_the_database_still_show_after_switching_to_s3(client, item, as_admin, request):
    image_id = add_picture(client, as_admin, item, PNG + b"before").json()["image_ids"][0]
    s3 = request.getfixturevalue("s3")  # switch only now
    url = f"/api/items/{item['id']}/images/{image_id}"
    assert client.get(url, headers=as_admin).content == PNG + b"before"
    client.delete(url, headers=as_admin)
    assert files(s3) == []


def test_nothing_is_saved_when_s3_cannot_be_reached(client, s3, item, as_admin, monkeypatch):
    monkeypatch.setattr(storage, "get_settings", lambda: settings(PICTURE_STORAGE="s3", PICTURE_BUCKET="no-such"))
    assert add_picture(client, as_admin, item).status_code == 503
    assert client.put("/api/auth/photo", content=PNG, headers=as_admin).status_code == 503
    assert client.get(f"/api/items/{item['id']}", headers=as_admin).json()["image_ids"] == []
    assert client.get("/api/auth/me", headers=as_admin).json()["photo_version"] == 0


def test_a_missing_file_is_reported_not_shown_empty(client, s3, item, session, as_admin):
    image_id = add_picture(client, as_admin, item).json()["image_ids"][0]
    s3.delete_object(Bucket=BUCKET, Key=files(s3)[0])
    assert client.get(f"/api/items/{item['id']}/images/{image_id}", headers=as_admin).status_code == 503


def test_the_database_is_the_default(client, item, session, as_admin):
    assert settings().PICTURE_STORAGE == "db"
    image_id = add_picture(client, as_admin, item).json()["image_ids"][0]
    row = session.get(ItemImage, image_id)
    assert (row.data, row.s3_key) == (PNG, "")


@pytest.mark.parametrize("values", [{"PICTURE_STORAGE": "s3", "PICTURE_BUCKET": ""}, {"PICTURE_STORAGE": "disk"}])
def test_the_app_refuses_storage_settings_that_cannot_work(values):
    with pytest.raises(ValidationError):
        settings(**values)
