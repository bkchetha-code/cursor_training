"""SQLite helpers — users table only for this step."""

from __future__ import annotations

import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash


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
