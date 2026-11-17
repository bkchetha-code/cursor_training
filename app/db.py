"""SQLite helpers — users + monitored servers."""

from __future__ import annotations

import re
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

_HOST_RE = re.compile(
    r"^(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?|"
    r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d?\d)|localhost)$"
)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            ssh_user TEXT NOT NULL DEFAULT 'root',
            auth_type TEXT NOT NULL DEFAULT 'key',
            key_path TEXT,
            password TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    _seed_admin(db)


def _seed_admin(db: sqlite3.Connection) -> None:
    """Create default admin once. Password comes from config; only the hash is stored."""
    row = db.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",),
    ).fetchone()
    if row is not None:
        return

    password = current_app.config["ADMIN_PASSWORD"]
    password_hash = generate_password_hash(password)
    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("admin", password_hash),
    )
    db.commit()


def get_user_by_username(username: str) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def update_user_password(user_id: int, password_hash: str) -> None:
    db = get_db()
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    db.commit()


def validate_host(host: str) -> bool:
    host = host.strip()
    if not host or len(host) > 255:
        return False
    return bool(_HOST_RE.match(host))


def list_servers() -> list[sqlite3.Row]:
    return get_db().execute(
        "SELECT id, name, host, ssh_user, auth_type, key_path, password, created_at "
        "FROM servers ORDER BY name COLLATE NOCASE"
    ).fetchall()


def get_server(server_id: int) -> sqlite3.Row | None:
    return get_db().execute(
        "SELECT id, name, host, ssh_user, auth_type, key_path, password, created_at "
        "FROM servers WHERE id = ?",
        (server_id,),
    ).fetchone()


def create_server(
    *,
    name: str,
    host: str,
    ssh_user: str,
    auth_type: str,
    key_path: str | None,
    password: str | None,
) -> int:
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO servers (name, host, ssh_user, auth_type, key_path, password)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, host, ssh_user, auth_type, key_path, password),
    )
    db.commit()
    return int(cur.lastrowid)


def update_server(
    server_id: int,
    *,
    name: str,
    host: str,
    ssh_user: str,
    auth_type: str,
    key_path: str | None,
    password: str | None,
) -> None:
    db = get_db()
    db.execute(
        """
        UPDATE servers
        SET name = ?, host = ?, ssh_user = ?, auth_type = ?, key_path = ?, password = ?
        WHERE id = ?
        """,
        (name, host, ssh_user, auth_type, key_path, password, server_id),
    )
    db.commit()


def delete_server(server_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    db.commit()
