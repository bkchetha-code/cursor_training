"""Unit tests for hashing, login, logout, and route protection."""

from __future__ import annotations

import time

from app.auth import hash_password, verify_password


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
    get_login = client.get("/login")
    assert get_login.status_code == 200
    html = get_login.get_data(as_text=True)
    # pull csrf from form
    token = _csrf_from(html)

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
    assert "No data yet" in body


def test_login_failure(client):
    token = _csrf_from(client.get("/login").get_data(as_text=True))
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong", "csrf_token": token},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Invalid username or password" in response.get_data(as_text=True)
    # still blocked from home
    assert client.get("/", follow_redirects=False).status_code == 302


def test_logout_clears_session(client):
    _login(client)
    home_html = client.get("/").get_data(as_text=True)
    csrf = _csrf_from(home_html)
    response = client.post(
        "/logout",
        data={"csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert client.get("/", follow_redirects=False).status_code == 302


def test_session_idle_timeout(client, app):
    _login(client)
    assert client.get("/").status_code == 200

    with client.session_transaction() as sess:
        sess["last_activity"] = time.time() - (app.config["SESSION_IDLE_SECONDS"] + 5)

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_session_cookie_httponly(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


def _csrf_from(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]


def _login(client) -> None:
    token = _csrf_from(client.get("/login").get_data(as_text=True))
    client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123", "csrf_token": token},
    )
