"""Unit tests for hashing, login, logout, and route protection."""

from __future__ import annotations

import time

from app.auth import hash_password, verify_password
from tests.test_helpers import csrf_from, login


def test_password_hash_verify_roundtrip():
    hashed = hash_password("secret-demo")
    assert hashed != "secret-demo"
    assert verify_password(hashed, "secret-demo")
    assert not verify_password(hashed, "wrong")


def test_protected_home_redirects_when_anonymous(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_success(client):
    token = csrf_from(client.get("/login").get_data(as_text=True))
    response = client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    home = client.get("/")
    assert home.status_code == 200
    body = home.get_data(as_text=True)
    assert "Host Monitor" in body
    assert "Monitoring dashboard" in body


def test_login_failure(client):
    token = csrf_from(client.get("/login").get_data(as_text=True))
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong", "csrf_token": token},
        follow_redirects=True,
    )
    assert "Invalid username or password" in response.get_data(as_text=True)
    assert client.get("/", follow_redirects=False).status_code == 302


def test_logout_clears_session(client):
    login(client)
    csrf = csrf_from(client.get("/").get_data(as_text=True))
    response = client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_session_idle_timeout(client, app):
    login(client)
    with client.session_transaction() as sess:
        sess["last_activity"] = time.time() - (app.config["SESSION_IDLE_SECONDS"] + 5)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_session_cookie_httponly(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


def test_change_password_success(client):
    login(client)
    token = csrf_from(client.get("/change-password").get_data(as_text=True))
    response = client.post(
        "/change-password",
        data={
            "csrf_token": token,
            "current_password": "test-pass-123",
            "new_password": "new-pass-456",
            "confirm_password": "new-pass-456",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    client.post("/logout", data={"csrf_token": csrf_from(client.get("/").get_data(as_text=True))})
    token = csrf_from(client.get("/login").get_data(as_text=True))
    ok = client.post(
        "/login",
        data={"username": "admin", "password": "new-pass-456", "csrf_token": token},
        follow_redirects=False,
    )
    assert ok.status_code == 302


def test_change_password_rejects_short(client):
    login(client)
    token = csrf_from(client.get("/change-password").get_data(as_text=True))
    response = client.post(
        "/change-password",
        data={
            "csrf_token": token,
            "current_password": "test-pass-123",
            "new_password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )
    assert "at least 8 characters" in response.get_data(as_text=True)
