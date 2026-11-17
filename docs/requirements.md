# PRD: Demo Monitoring Infrastructure (Linux Servers)

## 1. Overview

A **local demo** web app for internal L1/L2/L3 and app/infra teams to view Linux server metrics in a **read-only UI**, without SSH-ing into each host for routine checks.

**Goal:** Replace ad-hoc server logins for real-time CPU, memory, network, ports, disk, processes, and uptime with a simple Flask dashboard.

**Deployment:** Run only on the machine where Cursor is running (localhost). No production hardening required.

---

## 2. Users

| Role | Access |
|------|--------|
| Internal L1 / L2 / L3 | Read-only metrics views after sign-in |
| Infrastructure & application teams | Same — single shared demo account |

Multi-user roles and RBAC are **out of scope**.

---

## 3. Core Features

### 3.1 Read-only UI

- Attractive, simple Flask-served UI (HTML/CSS/JS templates).
- All metric screens are **view-only** (no remote shell, no config changes on targets).
- Server inventory CRUD (add / edit / delete / list) is allowed for the signed-in admin so the demo can manage what is monitored.

### 3.2 Sign-in

- Default username: `admin`.
- Password stored as a **hash** (e.g. Werkzeug/passlib); never plain text.
- Session-based login with **logout**.
- Simple **session timeout** (e.g. 30 minutes idle).
- Optional **change password** for the admin user (demo-level).

### 3.3 Add / manage Linux servers

- Provision to **add**, **edit**, **delete**, and **list** Linux servers to monitor.
- Store per server:
  - Display name
  - Hostname or IP
  - SSH user
  - Auth: SSH private key path **or** password (demo only; local SQLite)
- Connection method for the demo: **agentless over SSH** (app runs remote read-only commands). Localhost may be added as a server for easiest testing.

### 3.4 Metrics (per server)

| Metric | What to show |
|--------|----------------|
| CPU | Usage % |
| Memory | Used / free (and % if easy) |
| Network | Basic I/O (e.g. RX/TX rates or counters) |
| Ports | Listening / open ports summary |
| Disk | Usage per mount (used / free / %) |
| Processes | Short top process list (CPU/mem) |
| Uptime | Host uptime |

### 3.5 Refresh / “real time”

- **Periodic polling** (default every **5–10 seconds**), not true streaming.
- **Manual refresh** control on detail views.
- Auto-refresh can be toggled on/off in the UI if simple to add.

### 3.6 UI layout

1. **Dashboard** — overview of all monitored servers (status + key metrics summary).
2. **Server detail** — full metrics for one host (CPU, memory, network, ports, disk, processes, uptime).

---

## 4. Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3 |
| Web | Flask |
| UI | Flask templates + CSS (attractive, readable; keep minimal) |
| DB | SQLite (servers + hashed admin password) |
| Remote access | SSH (e.g. Paramiko) for metric collection |
| Run target | Localhost only |

---

## 5. Minimal local run (demo)

```text
1. Create venv and install deps (Flask, and SSH/hash libs as needed)
2. Initialize SQLite / seed admin user (admin + hashed password)
3. python app.py   # binds 0.0.0.0:5243
4. Open http://<host-ip>:5243 (or http://127.0.0.1:5243 locally)
5. Sign in → add a Linux server (or localhost) → view dashboard / detail
```

No Docker. No cloud deploy. No external monitoring agents required for the demo.

---

## 6. Non-functional (demo-level)

- **Security:** Read-only remote commands; hashed password; demo binds `0.0.0.0:5243` for multi-host access (not production-hardened).
- **Reliability:** If SSH fails, show clear error on that server card/detail; do not crash the app.
- **Performance:** Poll a small number of servers (demo scale: ~1–5 hosts).

---

## 7. Out of scope

- Alerts / thresholds / email / Slack
- Historical graphs or long-term metric storage
- Windows (or non-Linux) hosts
- Multi-user accounts, SSO, LDAP, RBAC
- Agents installed on every server
- Production TLS, HA, or multi-instance deploy

---

## 8. Acceptance criteria (demo)

- [ ] User can sign in as `admin` with hashed password verification
- [ ] User can log out; idle session expires
- [ ] User can add / edit / delete / list Linux servers
- [ ] Dashboard lists servers with summary status/metrics
- [ ] Detail page shows CPU, memory, network, ports, disk, processes, uptime
- [ ] Metrics refresh via polling (5–10s) and manual refresh
- [ ] UI is read-only for metrics; app runs locally via Flask
- [ ] SSH failure is surfaced in the UI without taking down the app
