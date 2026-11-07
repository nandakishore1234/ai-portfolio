from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.config import DATA_DIR, settings

logger = logging.getLogger(__name__)
DB_PATH = DATA_DIR / "app.db"
_PBKDF2_ROUNDS = 120_000

_ASSETS_SQL = """
CREATE TABLE IF NOT EXISTS assets (
    id BIGSERIAL PRIMARY KEY,
    room TEXT NOT NULL,
    kind TEXT NOT NULL,
    identity TEXT NOT NULL DEFAULT '',
    storage_path TEXT NOT NULL,
    public_url TEXT NOT NULL DEFAULT '',
    mime_type TEXT NOT NULL DEFAULT 'audio/wav',
    size_bytes BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_ADMINS_SQL = """
CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def postgres_url() -> str:
    url = (getattr(settings, "database_url", "") or "").strip()
    if not url.lower().startswith(("postgres://", "postgresql://")):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL connection string. SQLite is not used.")
    return url


def connect(*, rows: bool = False):
    kwargs = {"row_factory": dict_row} if rows else {}
    return psycopg.connect(postgres_url(), **kwargs)


def _serialize(row) -> dict:
    data = dict(row)
    created = data.get("created_at")
    if hasattr(created, "isoformat"):
        data["created_at"] = created.isoformat()
    return data


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS).hex()
    return f"pbkdf2_sha256${_PBKDF2_ROUNDS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, rounds, salt, digest = stored.split("$", 3)
        check = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(rounds),
        ).hex()
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(check, digest)


def _seed_admin(conn) -> None:
    username = (settings.admin_username or "nandu").strip()
    password = settings.admin_password or "nandu123"
    if not username or not password:
        raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set to seed the admins table.")
    exists = conn.execute("SELECT 1 FROM admins WHERE username = %s", (username,)).fetchone()
    if exists:
        return
    conn.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        (username, hash_password(password)),
    )
    logger.info("Seeded admin user %s in PostgreSQL", username)


def init_db() -> None:
    try:
        with connect() as conn:
            conn.execute(_ASSETS_SQL)
            conn.execute(_ADMINS_SQL)
            _seed_admin(conn)
            conn.commit()
    except Exception as exc:
        raise RuntimeError(
            "Could not connect to PostgreSQL with DATABASE_URL. "
            "Confirm database nanda_port is running for user nandu."
        ) from exc
    logger.info("Using PostgreSQL for assets and admin users")


def get_admin(username: str) -> dict | None:
    with connect(rows=True) as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM admins WHERE username = %s",
            (username.strip(),),
        ).fetchone()
        return dict(row) if row else None


def insert_asset(
    *,
    room: str,
    kind: str,
    storage_path: str,
    public_url: str = "",
    identity: str = "",
    mime_type: str = "audio/wav",
    size_bytes: int = 0,
) -> int:
    created = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        row = conn.execute(
            """
            INSERT INTO assets (room, kind, identity, storage_path, public_url, mime_type, size_bytes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (room, kind, identity, storage_path, public_url, mime_type, size_bytes, created),
        ).fetchone()
        conn.commit()
        return int(row[0])


def get_asset(asset_id: int) -> dict | None:
    with connect(rows=True) as conn:
        row = conn.execute(
            """
            SELECT id, room, kind, identity, storage_path, public_url, mime_type, size_bytes, created_at
            FROM assets WHERE id = %s
            """,
            (asset_id,),
        ).fetchone()
        return _serialize(row) if row else None


def list_assets(limit: int = 100) -> list[dict]:
    with connect(rows=True) as conn:
        rows = conn.execute(
            """
            SELECT id, room, kind, identity, storage_path, public_url, mime_type, size_bytes, created_at
            FROM assets ORDER BY id DESC LIMIT %s
            """,
            (limit,),
        ).fetchall()
        return [_serialize(row) for row in rows]


def db_path() -> Path:
    return DB_PATH
