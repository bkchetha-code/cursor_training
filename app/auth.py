"""Auth helpers — hashed passwords, sessions, CSRF, idle timeout."""

from __future__ import annotations

import secrets
import time
from functools import wraps
from typing import Callable, TypeVar

from flask import current_app, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

F = TypeVar("F", bound=Callable[..., object])


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def login_user(user_id: int, username: str) -> None:
    session.clear()
    session["user_id"] = user_id
    session["username"] = username
    session["last_activity"] = time.time()
    session.permanent = True


def logout_user() -> None:
    session.clear()


def is_authenticated() -> bool:
    return "user_id" in session


def touch_session() -> None:
    if is_authenticated():
        session["last_activity"] = time.time()


def session_expired() -> bool:
    if not is_authenticated():
        return False
    last = session.get("last_activity")
    if last is None:
        return True
    timeout = current_app.config["SESSION_IDLE_SECONDS"]
    return (time.time() - float(last)) > timeout


def issue_csrf_token() -> str:
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    return token


def validate_csrf(token: str | None) -> bool:
    expected = session.get("csrf_token")
    if not expected or not token:
        return False
    return secrets.compare_digest(expected, token)


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session_expired():
            logout_user()
            return redirect(url_for("main.login", next=request.path))
        if not is_authenticated():
            return redirect(url_for("main.login", next=request.path))
        touch_session()
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]
