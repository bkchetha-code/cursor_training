"""Agentless metric collection — allowlisted read-only commands only."""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any, Callable

from app import metrics as parsers

# Security: fixed allowlist only — never interpolate user input into commands.
ALLOWED_COMMANDS: dict[str, str] = {
    "cpu": "cat /proc/stat",
    "memory": "cat /proc/meminfo",
    "uptime": "cat /proc/uptime",
    "load": "cat /proc/loadavg",
    "disk": "df -P -B1",
    "network": "cat /proc/net/dev",
    "ports": "ss -lntu",
    "processes": "ps -eo pid,comm,%cpu,%mem --sort=-%cpu",
}

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_local(host: str) -> bool:
    h = host.strip().lower()
    if h in _LOCAL_HOSTS:
        return True
    try:
        return host in {socket.gethostname(), socket.getfqdn()}
    except OSError:
        return False


def _run_local(command_key: str) -> str:
    if command_key not in ALLOWED_COMMANDS:
        raise ValueError("command not allowlisted")
    # Prefer direct /proc reads where possible (no shell).
    if command_key == "cpu":
        return Path("/proc/stat").read_text(encoding="utf-8", errors="replace")
    if command_key == "memory":
        return Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace")
    if command_key == "uptime":
        return Path("/proc/uptime").read_text(encoding="utf-8", errors="replace")
    if command_key == "load":
        return Path("/proc/loadavg").read_text(encoding="utf-8", errors="replace")
    if command_key == "network":
        return Path("/proc/net/dev").read_text(encoding="utf-8", errors="replace")
    if command_key == "disk":
        import subprocess

        return subprocess.check_output(
            ["df", "-P", "-B1"], text=True, timeout=5
        )
    if command_key == "ports":
        import subprocess

        return subprocess.check_output(
            ["ss", "-lntu"], text=True, timeout=5
        )
    if command_key == "processes":
        import subprocess

        out = subprocess.check_output(
            ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
            text=True,
            timeout=5,
        )
        # truncate like head
        lines = out.splitlines()
        return "\n".join(lines[:11])
    raise ValueError("command not allowlisted")


def _run_ssh(server: dict[str, Any], command_key: str) -> str:
    if command_key not in ALLOWED_COMMANDS:
        raise ValueError("command not allowlisted")
    command = ALLOWED_COMMANDS[command_key]
    # Security: reject if allowlisted string somehow gained shell metacharacters
    if any(c in command for c in ";|&`$<>"):
        raise ValueError("unsafe command blocked")

    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs: dict[str, Any] = {
        "hostname": server["host"],
        "username": server["ssh_user"],
        "timeout": 8,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if server.get("auth_type") == "password":
        connect_kwargs["password"] = server.get("password") or ""
    else:
        key_path = server.get("key_path") or ""
        if not key_path:
            raise ConnectionError("SSH key path required")
        connect_kwargs["key_filename"] = key_path

    try:
        client.connect(**connect_kwargs)
        _stdin, stdout, stderr = client.exec_command(command, timeout=8)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        if code != 0 and not out:
            raise ConnectionError(err.strip() or f"remote exit {code}")
        return out
    finally:
        client.close()


_PARSERS: dict[str, Callable[[str], dict[str, Any]]] = {
    "cpu": parsers.parse_cpu,
    "memory": parsers.parse_memory,
    "uptime": parsers.parse_uptime,
    "load": parsers.parse_loadavg,
    "disk": parsers.parse_disk,
    "network": parsers.parse_network,
    "ports": parsers.parse_ports,
    "processes": parsers.parse_processes,
}


def collect_metrics(server: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect all metrics for a server row dict, or localhost if None."""
    host = (server or {}).get("host", "localhost")
    result: dict[str, Any] = {
        "host": host,
        "name": (server or {}).get("name", "localhost"),
        "ok": True,
        "error": None,
        "metrics": {},
    }
    runner = _run_local if server is None or _is_local(host) else (
        lambda key: _run_ssh(server, key)
    )
    try:
        for key, parse in _PARSERS.items():
            raw = runner(key)
            result["metrics"][key] = parse(raw)
    except Exception as exc:  # noqa: BLE001 — surface any collector failure in UI
        result["ok"] = False
        result["error"] = str(exc)
    return result


def collect_summary(server: dict[str, Any] | None = None) -> dict[str, Any]:
    full = collect_metrics(server)
    m = full.get("metrics") or {}
    cpu = (m.get("cpu") or {}).get("usage_percent")
    mem = (m.get("memory") or {}).get("used_percent")
    return {
        "id": (server or {}).get("id"),
        "name": full["name"],
        "host": full["host"],
        "ok": full["ok"],
        "error": full["error"],
        "cpu_percent": cpu,
        "mem_percent": mem,
        # never expose secrets
    }
