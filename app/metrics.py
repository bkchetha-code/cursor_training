"""Parse read-only host metric command outputs."""

from __future__ import annotations

from typing import Any


def _truncate(text: str, limit: int = 64_000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


def parse_cpu(stat_text: str) -> dict[str, Any]:
    """Parse first `cpu ` line from /proc/stat into approximate idle/busy %."""
    text = _truncate(stat_text)
    for line in text.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            values = [int(x) for x in parts[1:8]]
            total = sum(values)
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            busy = max(total - idle, 0)
            pct = round((busy / total) * 100, 1) if total else 0.0
            return {"usage_percent": pct, "raw_total": total, "raw_idle": idle}
    return {"usage_percent": None, "error": "cpu line not found"}


def parse_memory(meminfo_text: str) -> dict[str, Any]:
    text = _truncate(meminfo_text)
    data: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        num = rest.strip().split()[0]
        if num.isdigit():
            data[key] = int(num) * 1024  # kB → bytes
    total = data.get("MemTotal")
    available = data.get("MemAvailable") or data.get("MemFree")
    if total is None or available is None:
        return {"error": "meminfo incomplete"}
    used = max(total - available, 0)
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": available,
        "used_percent": round((used / total) * 100, 1) if total else 0.0,
    }


def parse_uptime(uptime_text: str) -> dict[str, Any]:
    text = _truncate(uptime_text).strip().split()
    if not text:
        return {"error": "empty uptime"}
    seconds = float(text[0])
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return {
        "seconds": seconds,
        "human": f"{days}d {hours}h {minutes}m {secs}s",
    }


def parse_loadavg(load_text: str) -> dict[str, Any]:
    parts = _truncate(load_text).split()
    if len(parts) < 3:
        return {"error": "loadavg incomplete"}
    return {"load_1": parts[0], "load_5": parts[1], "load_15": parts[2]}


def parse_disk(df_text: str) -> dict[str, Any]:
    text = _truncate(df_text)
    mounts: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line in lines[1:]:
        cols = line.split()
        if len(cols) < 6:
            continue
        total, used, avail, pct, mount = cols[1], cols[2], cols[3], cols[4], cols[5]
        mounts.append(
            {
                "mount": mount,
                "total_bytes": int(total),
                "used_bytes": int(used),
                "free_bytes": int(avail),
                "used_percent": pct.rstrip("%"),
            }
        )
        if len(mounts) >= 20:
            break
    root = next((m for m in mounts if m["mount"] == "/"), mounts[0] if mounts else None)
    return {"mounts": mounts, "root": root}


def parse_network(netdev_text: str) -> dict[str, Any]:
    text = _truncate(netdev_text)
    interfaces: list[dict[str, Any]] = []
    for line in text.splitlines():
        if ":" not in line or line.strip().startswith("Inter") or "face" in line:
            continue
        name, rest = line.split(":", 1)
        cols = rest.split()
        if len(cols) < 16:
            continue
        iface = name.strip()
        if iface == "lo":
            continue
        interfaces.append(
            {
                "name": iface,
                "rx_bytes": int(cols[0]),
                "tx_bytes": int(cols[8]),
            }
        )
        if len(interfaces) >= 16:
            break
    rx = sum(i["rx_bytes"] for i in interfaces)
    tx = sum(i["tx_bytes"] for i in interfaces)
    return {"interfaces": interfaces, "rx_bytes": rx, "tx_bytes": tx}


def parse_ports(ss_text: str) -> dict[str, Any]:
    text = _truncate(ss_text, 32_000)
    listening: list[str] = []
    tcp = udp = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        proto = parts[0].lower() if parts else ""
        if proto.startswith("tcp"):
            tcp += 1
        elif proto.startswith("udp"):
            udp += 1
        # local address usually column 4 for ss
        local = parts[4] if len(parts) > 4 else (parts[3] if len(parts) > 3 else "")
        if local and local not in listening:
            listening.append(local)
        if len(listening) >= 50:
            break
    return {"tcp": tcp, "udp": udp, "listening": listening[:40]}


def parse_processes(ps_text: str) -> dict[str, Any]:
    text = _truncate(ps_text, 32_000)
    rows: list[dict[str, str]] = []
    lines = text.splitlines()
    for line in lines[1:]:
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        rows.append(
            {
                "pid": parts[0],
                "comm": parts[1][:64],
                "cpu": parts[2],
                "mem": parts[3].split()[0] if parts[3] else "",
            }
        )
        if len(rows) >= 10:
            break
    return {"top": rows}
