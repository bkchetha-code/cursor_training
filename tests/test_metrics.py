"""Parser and collector unit tests."""

from __future__ import annotations

from unittest.mock import patch

from app.collector import ALLOWED_COMMANDS, collect_metrics
from app.metrics import (
    parse_cpu,
    parse_disk,
    parse_loadavg,
    parse_memory,
    parse_network,
    parse_ports,
    parse_processes,
    parse_uptime,
)
from tests.test_helpers import login


def test_parse_cpu_memory_uptime_load():
    cpu = parse_cpu("cpu  100 0 50 850 0 0 0\ncpu0 10 0 5 85 0 0 0\n")
    assert cpu["usage_percent"] == 15.0
    mem = parse_memory("MemTotal: 1000000 kB\nMemAvailable: 400000 kB\n")
    assert mem["used_percent"] == 60.0
    up = parse_uptime("3661.10 1000.00\n")
    assert "1h" in up["human"] or "0d 1h" in up["human"]
    load = parse_loadavg("0.10 0.20 0.30 1/100 1\n")
    assert load["load_1"] == "0.10"


def test_parse_disk_network_ports_processes():
    disk = parse_disk(
        "Filesystem 1024-blocks Used Available Capacity Mounted\n"
        "/dev/sda1 1000 400 600 40% /\n"
    )
    assert disk["root"]["used_percent"] == "40"
    net = parse_network(
        "Inter-|   Receive\n face |bytes\n  eth0: 1000 0 0 0 0 0 0 0 2000 0 0 0 0 0 0 0\n"
    )
    assert net["rx_bytes"] == 1000
    assert net["tx_bytes"] == 2000
    ports = parse_ports("tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\nudp UNCONN 0 0 0.0.0.0:68 0.0.0.0:*\n")
    assert ports["tcp"] == 1 and ports["udp"] == 1
    procs = parse_processes("PID COMMAND %CPU %MEM\n1 systemd 0.0 0.1\n2 bash 1.2 0.5\n")
    assert procs["top"][0]["comm"] == "systemd"


def test_oversized_output_truncated():
    huge = "cpu  1 0 0 1 0 0 0\n" + ("x" * 100_000)
    assert parse_cpu(huge)["usage_percent"] is not None


def test_allowlist_keys():
    assert "cpu" in ALLOWED_COMMANDS
    assert ";" not in ALLOWED_COMMANDS["cpu"]


def test_collect_local_metrics():
    data = collect_metrics(None)
    assert data["ok"] is True
    assert "cpu" in data["metrics"]
    assert "memory" in data["metrics"]


def test_collect_ssh_failure_does_not_raise():
    server = {
        "id": 1,
        "name": "x",
        "host": "203.0.113.10",
        "ssh_user": "root",
        "auth_type": "password",
        "password": "nope",
        "key_path": None,
    }
    with patch("app.collector._run_ssh", side_effect=ConnectionError("auth failed")):
        data = collect_metrics(server)
    assert data["ok"] is False
    assert "auth failed" in data["error"]


def test_api_metrics_requires_auth(client):
    assert client.get("/api/metrics").status_code in {302, 401}


def test_api_metrics_ok_when_logged_in(client):
    login(client)
    response = client.get("/api/metrics")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert "metrics" in payload


def test_dashboard_shows_localhost_summary(client):
    login(client)
    html = client.get("/").get_data(as_text=True)
    assert "localhost" in html
    assert "id_rsa" not in html
    assert "ssh_password" not in html
