# TODO: Demo Monitoring Infrastructure (Linux)

Small, AI-friendly increments for a **local Flask demo**. Check items as you complete them.  
Reference: [requirements.md](./requirements.md)

---

## 1. Project initialization and basic UI

- [x] Create repo layout (`app/`, `tests/`, `docs/`, `templates/`, `static/`)
- [x] Add `requirements.txt` (Flask, pytest minimal set) and `.gitignore` (venv, `__pycache__`, `.env`, `*.db`)
- [x] **Security:** Do not commit secrets; document that `.env` / DB stay local
- [x] Scaffold minimal Flask app that binds to `0.0.0.0:5243` (reachable from other hosts)
- [x] **Security:** Document multi-host bind; keep secrets out of git (demo, not production-hardened)
- [x] Add base layout template + simple attractive CSS (nav shell, placeholder home)
- [x] Add read-only home/landing page (“Demo Monitoring” branding)
- [x] **Docs:** Short `README.md` — venv, install, `python app.py`, open `http://<host-ip>:5243`

---

## 2. Sign-in and unit tests

- [x] Add SQLite + user model/table (username, password hash only)
- [x] Seed default user `admin` with **hashed** password on first run
- [x] **Security:** Never store or log plain-text passwords; use Werkzeug (or equivalent) hashing
- [x] Implement login form + session cookie on success
- [x] **Security:** Use Flask `SECRET_KEY` from env (with safe local default for demo only); document rotation
- [x] Protect routes: redirect unauthenticated users to login
- [x] Implement logout (clear session)
- [x] Add idle session timeout (~30 minutes)
- [x] **Security:** Session cookie `HttpOnly`; document CSRF as demo-optional / add simple CSRF if easy
- [x] Unit tests: hash verify, login success/fail, logout, protected route redirect
- [x] **Docs:** Document default `admin` credentials location (env/seed script), change-password later, and how to run `pytest`

---

## 3. CI/CD (GitHub Actions) — early, keep green

- [x] Add `.github/workflows/ci.yml` — install deps, run `pytest` on push/PR
- [x] **Security:** No secrets in workflow; use dummy env for tests only
- [x] Pin or constrain Python version in CI (e.g. 3.11/3.12)
- [x] **Docs:** One paragraph in README — what CI runs and how to check status

---

## 4. Change password (demo admin)

- [x] Change-password form (current + new + confirm)
- [x] **Security:** Re-verify current password; reject weak/empty new password (minimal rules)
- [x] Unit tests for change-password success/fail
- [x] **Docs:** Update README with change-password steps

---

## 5. Server inventory (CRUD) — no SSH yet

- [x] SQLite table for servers: name, host/IP, SSH user, auth type, key path or password field
- [x] **Security:** Prefer key path over storing SSH passwords; if password stored, note demo-only risk in docs
- [x] List servers page (empty state OK)
- [x] Add server form + create action
- [x] Edit server form + update action
- [x] Delete server with simple confirm
- [x] **Security:** All CRUD behind login; validate host/IP input (basic); escape output in templates (Jinja autoescape on)
- [x] Unit tests: CRUD happy path + unauthorized access denied
- [x] **Docs:** How to add a server (fields explained); warn not for production secrets

---

## 6. SSH collector skeleton (read-only)

- [x] Add Paramiko (or similar) dependency
- [x] Implement connect + run **allowlisted** read-only commands only
- [x] **Security:** Hard deny shell metacharacters / arbitrary user commands; fixed command list only
- [x] Return structured errors on auth/timeout/unreachable (no app crash)
- [x] Unit tests with mocked SSH (success + failure)
- [x] **Docs:** Note agentless SSH, required remote permissions, localhost testing tip

---

## 7. Metrics: CPU, memory, uptime

- [x] Collect and parse CPU %, memory used/free, uptime via allowlisted commands
- [x] **Security:** Keep command allowlist; no writable remote ops
- [x] Show values on server detail page (placeholders → real data)
- [x] Unit tests for parsers (sample command output fixtures)
- [x] **Docs:** Brief metric definitions (what each number means)

---

## 8. Metrics: disk, network, ports, processes

- [x] Disk usage per mount
- [x] Network basic I/O counters or rates
- [x] Listening/open ports summary
- [x] Short top process list (CPU/mem)
- [x] **Security:** Read-only commands only; truncate/limit process & port output size
- [x] Unit tests for each parser + oversized-output handling
- [x] **Docs:** Update metrics section with examples / limitations

---

## 9. Dashboard overview

- [x] Dashboard cards/rows: all servers + summary status + key metrics
- [x] Show per-server error state when SSH fails (app stays up)
- [x] **Security:** No sensitive SSH secrets rendered in UI
- [x] Unit/integration tests: dashboard with mocked collectors
- [x] **Docs:** Screenshot or short walkthrough of dashboard → detail

---

## 10. Refresh / polling UI

- [x] Manual refresh on detail (and dashboard if simple)
- [x] Auto-poll every 5–10 seconds (toggle on/off optional)
- [x] **Security:** Poll endpoints require auth; rate-limit lightly if trivial
- [x] Basic test or manual checklist for refresh behavior
- [x] **Docs:** Document poll interval and toggle

---

## 11. Polish, local demo checklist, CI green

- [x] UI pass: readable empty/error states; consistent layout
- [x] **Security:** Final pass — `0.0.0.0:5243` bind documented, hashed passwords, no secrets in git, allowlisted SSH only
- [x] Ensure GitHub Actions CI still passes (`pytest` + lint if added)
- [x] **Docs:** Final README demo path — install → seed → run → login → add server → view metrics
- [x] Cross-check [requirements.md](./requirements.md) acceptance criteria and mark done there

---

## Out of scope (do not implement)

- Alerts, email, historical graphs
- Windows hosts, multi-user RBAC, SSO
- Docker / cloud deploy / agents on every host
