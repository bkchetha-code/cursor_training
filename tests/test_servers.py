"""Server inventory CRUD tests."""

from __future__ import annotations

from tests.test_helpers import csrf_from, login


def test_servers_require_login(client):
    assert client.get("/servers", follow_redirects=False).status_code == 302


def test_server_crud_happy_path(client):
    login(client)
    token = csrf_from(client.get("/servers/new").get_data(as_text=True))
    created = client.post(
        "/servers/new",
        data={
            "csrf_token": token,
            "name": "lab-1",
            "host": "10.0.0.5",
            "ssh_user": "ubuntu",
            "auth_type": "key",
            "key_path": "/tmp/id_rsa",
            "password": "",
        },
        follow_redirects=False,
    )
    assert created.status_code == 302
    listing = client.get("/servers")
    assert "lab-1" in listing.get_data(as_text=True)
    assert "10.0.0.5" in listing.get_data(as_text=True)

    # edit
    edit_page = client.get("/servers/1/edit")
    token = csrf_from(edit_page.get_data(as_text=True))
    client.post(
        "/servers/1/edit",
        data={
            "csrf_token": token,
            "name": "lab-1b",
            "host": "10.0.0.6",
            "ssh_user": "ubuntu",
            "auth_type": "key",
            "key_path": "/tmp/id_rsa",
            "password": "",
        },
    )
    assert "lab-1b" in client.get("/servers").get_data(as_text=True)

    # delete
    token = csrf_from(client.get("/servers").get_data(as_text=True))
    client.post("/servers/1/delete", data={"csrf_token": token})
    assert "lab-1b" not in client.get("/servers").get_data(as_text=True)


def test_invalid_host_rejected(client):
    login(client)
    token = csrf_from(client.get("/servers/new").get_data(as_text=True))
    response = client.post(
        "/servers/new",
        data={
            "csrf_token": token,
            "name": "bad",
            "host": "not a host!!",
            "ssh_user": "root",
            "auth_type": "key",
            "key_path": "/tmp/k",
            "password": "",
        },
        follow_redirects=True,
    )
    assert "valid hostname" in response.get_data(as_text=True)
