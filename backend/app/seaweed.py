from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.config import DATA_DIR, settings

logger = logging.getLogger(__name__)


def _filer_base() -> str:
    return (settings.seaweedfs_filer_url or "http://127.0.0.1:8888").rstrip("/")


def _prefix() -> str:
    prefix = (settings.seaweedfs_prefix or "/nanda-calls").strip()
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/")


def public_url(storage_path: str) -> str:
    return f"{_filer_base()}{storage_path}"


def upload_bytes(storage_path: str, data: bytes, content_type: str = "audio/wav") -> str:
    """PUT a file to the SeaweedFS filer. Returns the filer path."""
    if not storage_path.startswith("/"):
        storage_path = f"/{storage_path}"
    url = f"{_filer_base()}{storage_path}"
    try:
        response = httpx.put(
            url,
            content=data,
            headers={"Content-Type": content_type},
            timeout=60.0,
        )
        response.raise_for_status()
        logger.info("Uploaded %s (%s bytes) to SeaweedFS", storage_path, len(data))
        return storage_path
    except Exception as exc:
        fallback = DATA_DIR / "recordings" / storage_path.lstrip("/").replace("/", "_")
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.write_bytes(data)
        logger.warning("SeaweedFS upload failed (%s); saved locally at %s", exc, fallback)
        return str(fallback)


def call_object_path(room: str, identity: str) -> str:
    safe_room = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in room)[:80]
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in identity)[:40] or "track"
    return f"{_prefix()}/{safe_room}/{safe_id}.wav"
