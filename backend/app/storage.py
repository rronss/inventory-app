"""Where picture files are kept: in the database (the default) or in a private S3 bucket.

Each row notes where its own picture is, so pictures saved before a switch to S3 are still found.
Removing is done after the database commit: a file left behind is harmless, a missing one is a broken picture.
"""
import logging
import uuid
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from .config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def s3_client():
    # No keys here: boto3 finds credentials itself (on EC2, the server's role).
    return boto3.session.Session().client(
        "s3", config=Config(connect_timeout=5, read_timeout=10, retries={"max_attempts": 3})
    )


def store(picture, prefix: str, data: bytes, content_type: str) -> None:
    """Puts the picture where the settings say and notes it on the row. The caller commits."""
    settings = get_settings()
    if settings.PICTURE_STORAGE != "s3":
        picture.data, picture.s3_key = data, ""
        return
    key = f"{prefix}/{uuid.uuid4().hex}"  # a new name every time, so a file is never overwritten
    try:
        s3_client().put_object(Bucket=settings.PICTURE_BUCKET, Key=key, Body=data, ContentType=content_type)
    except (BotoCoreError, ClientError) as error:
        log.error("Could not save a picture to S3: %s", error)
        raise HTTPException(503, "The picture can't be saved right now") from error
    picture.data, picture.s3_key = b"", key


def read(picture) -> bytes:
    if not picture.s3_key:
        return picture.data
    try:
        return s3_client().get_object(Bucket=get_settings().PICTURE_BUCKET, Key=picture.s3_key)["Body"].read()
    except (BotoCoreError, ClientError) as error:
        log.error("Could not read picture %s from S3: %s", picture.s3_key, error)
        raise HTTPException(503, "The picture can't be read right now") from error


def discard(*keys: str) -> None:
    """Removes files that no row points to any more. An empty key means the picture was in the database."""
    for key in filter(None, keys):
        try:
            s3_client().delete_object(Bucket=get_settings().PICTURE_BUCKET, Key=key)
        except (BotoCoreError, ClientError) as error:
            log.warning("Left an unused file in S3, %s: %s", key, error)
