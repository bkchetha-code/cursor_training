"""Shared test helpers."""

from __future__ import annotations


def csrf_from(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    end = html.index('"', start)
    return html[start:end]


def login(client) -> None:
    token = csrf_from(client.get("/login").get_data(as_text=True))
    client.post(
        "/login",
        data={"username": "admin", "password": "test-pass-123", "csrf_token": token},
    )
