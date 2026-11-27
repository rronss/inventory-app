"""Slows down password guessing and mass sign-ups.

The counts are kept in memory: the app runs as a single process, and a restart clears them.
"""
import math
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

from .config import get_settings

LONGEST_WINDOW = 3600
MANY_KEYS = 10_000  # past this, forget the keys that have gone quiet, so made-up names cannot fill the memory


class Limiter:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.hits: dict[str, deque[float]] = {}
        self.lock = threading.Lock()  # sign-ins run in parallel threads

    def take(self, *rules: tuple[str, int, int]) -> None:
        """Counts one attempt against every (key, limit, seconds), or refuses and counts none."""
        with self.lock:
            now = self.clock()
            if len(self.hits) > MANY_KEYS:
                self.hits = {k: v for k, v in self.hits.items() if v and now - v[-1] < LONGEST_WINDOW}
            for key, limit, window in rules:
                seen = self.hits.setdefault(key, deque())
                while seen and now - seen[0] >= window:
                    seen.popleft()
                if len(seen) >= limit:
                    wait = math.ceil(window - (now - seen[0]))
                    minutes = math.ceil(wait / 60)
                    raise HTTPException(
                        429,
                        f"Too many attempts. Try again in {minutes} minute{'' if minutes == 1 else 's'}.",
                        headers={"Retry-After": str(wait)},
                    )
            for key, _, _ in rules:
                self.hits[key].append(now)

    def give_back(self, key: str) -> None:
        with self.lock:
            if self.hits.get(key):
                self.hits[key].pop()

    def forget(self, key: str) -> None:
        with self.lock:
            self.hits.pop(key, None)

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()


limiter = Limiter()


def client_address(request: Request) -> str:
    """The visitor's address. Each proxy of ours appends to X-Forwarded-For, so count from the right: whatever the
    visitor put there themselves is further left and is ignored."""
    hops = get_settings().TRUSTED_PROXIES
    if hops:
        chain = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if len(chain) >= hops:
            return chain[-hops]
    return request.client.host if request.client else "unknown"
