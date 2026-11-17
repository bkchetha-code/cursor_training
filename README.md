# Host Monitor (Linux demo)

Local Flask **Host Monitor** demo for read-only Linux server metrics (CPU, memory, network, ports, and more).  
Internal L1/L2/L3 use — **not** for production.

## Security (local demo)

- App binds to **`0.0.0.0:5243`** by default so other hosts can reach the demo UI.
- Keep secrets out of git: copy `.env.example` → `.env` if needed; never commit `.env` or `*.db`.
- `SECRET_KEY` from `FLASK_SECRET_KEY` (demo default only if unset — rotate for shared demos).
- Passwords stored as **Werkzeug hashes** only; never logged.
- Session cookie: **HttpOnly** + `SameSite=Lax`; idle timeout **30 minutes**.
- Simple CSRF tokens on login/logout forms (demo-level).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://<host-ip>:5243` (or http://127.0.0.1:5243 on this machine).

Sign in with default seeded user:

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `admin123` (or `ADMIN_PASSWORD` env at **first** DB seed) |

Override via env: `FLASK_HOST`, `FLASK_PORT`, `FLASK_SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_PATH`, `SESSION_IDLE_SECONDS`.

Change-password UI comes in a later TODO step.

## Tests

```bash
source .venv/bin/activate
pytest
```

## Project layout

```text
app/           Flask app factory, auth, db, routes
templates/     Jinja templates
static/        CSS / assets
tests/         Unit tests
docs/          PRD + TODO
```

## Docs

- [Requirements (PRD)](docs/requirements.md)
- [Implementation TODO](docs/TODO.md)
