from __future__ import annotations

import threading
from collections.abc import Iterable


def parse_keys(*values: str | None) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        for part in str(value).replace("\n", ",").split(","):
            key = part.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            keys.append(key)
    return keys


def is_retryable_provider_error(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    try:
        status_int = int(status) if status is not None else None
    except (TypeError, ValueError):
        status_int = None
    if status_int in {401, 403, 408, 429, 500, 502, 503, 504}:
        return True
    text = str(exc).lower()
    markers = (
        "429",
        "401",
        "403",
        "quota",
        "resource_exhausted",
        "rate limit",
        "rate-limit",
        "too many requests",
        "exceeded your current quota",
        "insufficient_quota",
        "invalid api key",
        "api key not valid",
        "unauthorized",
        "permission denied",
        "overloaded",
        "unavailable",
        "temporarily",
        "timeout",
        "timed out",
        "connection",
    )
    return any(marker in text for marker in markers)


class KeyPool:
    def __init__(self, keys: Iterable[str], *, name: str) -> None:
        self.name = name
        self.keys = [key.strip() for key in keys if key and key.strip()]
        if not self.keys:
            raise ValueError(f"No {name} API keys configured.")
        self._index = 0
        self._lock = threading.Lock()

    def current(self) -> str:
        with self._lock:
            return self.keys[self._index]

    def rotate(self) -> str:
        with self._lock:
            self._index = (self._index + 1) % len(self.keys)
            return self.keys[self._index]

    def prefer(self, key: str) -> None:
        with self._lock:
            if key in self.keys:
                self._index = self.keys.index(key)

    def snapshot_order(self) -> list[str]:
        with self._lock:
            start = self._index
        return [self.keys[(start + offset) % len(self.keys)] for offset in range(len(self.keys))]
