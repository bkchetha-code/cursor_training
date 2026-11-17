# Host Monitor (Linux demo)

Local Flask **Host Monitor** for read-only Linux metrics (CPU, memory, disk, load, network, ports, processes, uptime).  
Internal L1/L2/L3 demo — **not** for production.

Remote: `https://github.com/bkchetha-code/cursor_training.git`

## Security (demo)

- Binds **`0.0.0.0:5243`** so other hosts can reach the UI.
- Never commit `.env` or `*.db` (see `.gitignore`).
- `FLASK_SECRET_KEY` from env (demo default if unset — rotate for shared demos).
- Passwords stored as **Werkzeug hashes** only; never logged.
- Session: HttpOnly + SameSite=Lax; idle timeout 30 minutes; CSRF on forms.
- Metrics via **allowlisted** read-only commands only (local `/proc` or Paramiko SSH).
- Prefer SSH **key path** over storing passwords (demo-only if password auth used).
- UI never renders SSH secrets.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://<host-ip>:5243` → sign in → view localhost metrics → optionally **Servers** → add a host → open detail.

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `admin123` (or `ADMIN_PASSWORD` at first DB seed) |

Change password: nav **Password** (current + new ≥ 8 chars).

Env: `FLASK_HOST`, `FLASK_PORT` (5243), `FLASK_SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_PATH`, `SESSION_IDLE_SECONDS`.

## Metrics

| Panel | Meaning |
|-------|---------|
| CPU | Busy share from `/proc/stat` (approx %) |
| Memory | Used / available from `/proc/meminfo` |
| Disk | Root mount from `df -P -B1` |
| Load | 1 / 5 / 15 min from `/proc/loadavg` |
| Network | Sum RX/TX bytes from `/proc/net/dev` (excl. lo) |
| Ports | Listening TCP/UDP count from `ss -lntu` |
| Processes | Top CPU processes from `ps` |
| Uptime | From `/proc/uptime` |

Auto-refresh every **8s** (toggle / Refresh now). `/api/metrics` requires login and is lightly rate-limited.

## Servers

Add name, host/IP, SSH user, auth type (key path preferred, password demo-only). Localhost is always monitored without SSH.

## Tests & CI

```bash
pytest
```

GitHub Actions (`.github/workflows/ci.yml`) runs `pytest` on push/PR with Python **3.12** and dummy env vars only. Check the **Actions** tab on GitHub for status.

## Layout

```text
app/           Flask factory, auth, db, collector, metrics, routes
templates/     Jinja UI
static/        CSS + poll.js
tests/         Unit tests
docs/          PRD + TODO
.github/       CI workflow
```
