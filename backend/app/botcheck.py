"""Cloudflare Turnstile on sign-up. Off unless both keys are set."""
import json
import logging
import urllib.parse
import urllib.request

from fastapi import HTTPException

from .config import get_settings

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
log = logging.getLogger(__name__)


def check(token: str, address: str) -> None:
    secret = get_settings().TURNSTILE_SECRET_KEY
    if not secret:
        return
    refused = HTTPException(400, "Please complete the check that you are not a robot")
    if not token:
        raise refused
    body = urllib.parse.urlencode({"secret": secret, "response": token, "remoteip": address}).encode()
    try:
        with urllib.request.urlopen(VERIFY_URL, body, timeout=10) as response:
            passed = json.load(response).get("success") is True
    except (OSError, ValueError) as error:  # unreachable, or an answer that is not JSON
        log.error("Could not reach the bot check: %s", error)
        raise HTTPException(503, "Sign-up is unavailable right now. Please try again.") from error
    if not passed:
        raise refused
