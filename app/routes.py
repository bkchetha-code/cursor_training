"""HTTP routes — auth, server CRUD, metrics dashboard (read-only)."""

from __future__ import annotations

import time
from typing import Any

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.auth import (
    hash_password,
    is_authenticated,
    issue_csrf_token,
    login_required,
    login_user,
    logout_user,
    session_expired,
    touch_session,
    validate_csrf,
    verify_password,
)
from app.collector import collect_metrics, collect_summary
from app.db import (
    create_server,
    delete_server,
    get_server,
    get_user_by_id,
    get_user_by_username,
    list_servers,
    update_server,
    update_user_password,
    validate_host,
)

bp = Blueprint("main", __name__)

_LAST_POLL: dict[str, float] = {}
_MIN_POLL_SECONDS = 2.0


def _row_to_server(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "host": row["host"],
        "ssh_user": row["ssh_user"],
        "auth_type": row["auth_type"],
        "key_path": row["key_path"],
        "password": row["password"],
    }


def _public_server(row) -> dict[str, Any]:
    """UI-safe server fields — never expose SSH password/key material."""
    return {
        "id": row["id"],
        "name": row["name"],
        "host": row["host"],
        "ssh_user": row["ssh_user"],
        "auth_type": row["auth_type"],
        "has_key": bool(row["key_path"]),
        "has_password": bool(row["password"]),
    }


@bp.before_app_request
def enforce_idle_timeout():
    if request.endpoint in {None, "static", "main.login"}:
        return None
    if session_expired():
        logout_user()
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("main.login", next=request.path))
    if is_authenticated():
        touch_session()
    return None


@bp.get("/")
@login_required
def home():
    servers = list_servers()
    summaries = []
    # Always include localhost metrics for the demo host
    local = collect_summary(None)
    local["id"] = None
    local["name"] = "localhost"
    summaries.append(local)
    for row in servers:
        summaries.append(collect_summary(_row_to_server(row)))
    return render_template(
        "home.html",
        servers=[_public_server(s) for s in servers],
        summaries=summaries,
        poll_seconds=8,
    )


@bp.get("/api/metrics")
@login_required
def api_metrics():
    """JSON metrics for polling — auth required, lightly rate-limited."""
    key = str(session.get("user_id"))
    now = time.time()
    last = _LAST_POLL.get(key, 0)
    if now - last < _MIN_POLL_SECONDS:
        return jsonify({"ok": False, "error": "rate_limited"}), 429
    _LAST_POLL[key] = now

    server_id = request.args.get("server_id")
    if server_id in (None, "", "local", "localhost"):
        data = collect_metrics(None)
        data["server_id"] = None
        return jsonify(data)

    try:
        sid = int(server_id)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid server_id"}), 400
    row = get_server(sid)
    if row is None:
        return jsonify({"ok": False, "error": "not found"}), 404
    data = collect_metrics(_row_to_server(row))
    data["server_id"] = sid
    # strip any accidental secrets
    data.pop("password", None)
    return jsonify(data)


@bp.get("/servers/<int:server_id>")
@login_required
def server_detail(server_id: int):
    row = get_server(server_id)
    if row is None:
        flash("Server not found.", "warning")
        return redirect(url_for("main.home"))
    metrics = collect_metrics(_row_to_server(row))
    return render_template(
        "server_detail.html",
        server=_public_server(row),
        metrics=metrics,
        poll_seconds=8,
    )


@bp.get("/localhost")
@login_required
def localhost_detail():
    metrics = collect_metrics(None)
    server = {
        "id": None,
        "name": "localhost",
        "host": "127.0.0.1",
        "ssh_user": "-",
        "auth_type": "local",
        "has_key": False,
        "has_password": False,
    }
    return render_template(
        "server_detail.html",
        server=server,
        metrics=metrics,
        poll_seconds=8,
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated() and not session_expired():
        return redirect(url_for("main.home"))

    error = None
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            error = "Invalid form token. Please try again."
        else:
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = get_user_by_username(username)
            if user is None or not verify_password(user["password_hash"], password):
                error = "Invalid username or password."
            else:
                login_user(user["id"], user["username"])
                issue_csrf_token()
                flash("Signed in successfully.", "success")
                nxt = request.args.get("next") or url_for("main.home")
                if not nxt.startswith("/"):
                    nxt = url_for("main.home")
                return redirect(nxt)

    csrf_token = issue_csrf_token()
    return render_template("login.html", error=error, csrf_token=csrf_token)


@bp.post("/logout")
@login_required
def logout():
    if not validate_csrf(request.form.get("csrf_token")):
        flash("Invalid form token.", "warning")
        return redirect(url_for("main.home"))
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("main.login"))


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            error = "Invalid form token. Please try again."
        else:
            current = request.form.get("current_password") or ""
            new = request.form.get("new_password") or ""
            confirm = request.form.get("confirm_password") or ""
            user = get_user_by_id(int(session["user_id"]))
            if user is None or not verify_password(user["password_hash"], current):
                error = "Current password is incorrect."
            elif len(new) < 8:
                error = "New password must be at least 8 characters."
            elif new != confirm:
                error = "New password and confirmation do not match."
            else:
                update_user_password(user["id"], hash_password(new))
                flash("Password updated.", "success")
                return redirect(url_for("main.home"))
    return render_template(
        "change_password.html",
        error=error,
        csrf_token=issue_csrf_token(),
    )


@bp.get("/servers")
@login_required
def servers_list():
    rows = list_servers()
    return render_template(
        "servers.html",
        servers=[_public_server(s) for s in rows],
    )


@bp.route("/servers/new", methods=["GET", "POST"])
@login_required
def servers_new():
    error = None
    form = {
        "name": "",
        "host": "",
        "ssh_user": "root",
        "auth_type": "key",
        "key_path": "",
        "password": "",
    }
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            error = "Invalid form token."
        else:
            form = {k: (request.form.get(k) or "").strip() for k in form}
            form["password"] = request.form.get("password") or ""
            if not form["name"] or not form["host"] or not form["ssh_user"]:
                error = "Name, host, and SSH user are required."
            elif not validate_host(form["host"]):
                error = "Host must be a valid hostname or IPv4 address."
            elif form["auth_type"] not in {"key", "password"}:
                error = "Invalid auth type."
            elif form["auth_type"] == "key" and not form["key_path"]:
                error = "Key path is required for key auth."
            elif form["auth_type"] == "password" and not form["password"]:
                error = "Password is required for password auth."
            else:
                create_server(
                    name=form["name"],
                    host=form["host"],
                    ssh_user=form["ssh_user"],
                    auth_type=form["auth_type"],
                    key_path=form["key_path"] or None,
                    password=form["password"] if form["auth_type"] == "password" else None,
                )
                flash("Server added.", "success")
                return redirect(url_for("main.servers_list"))
    return render_template(
        "server_form.html",
        title="Add server",
        form=form,
        error=error,
        csrf_token=issue_csrf_token(),
        action=url_for("main.servers_new"),
    )


@bp.route("/servers/<int:server_id>/edit", methods=["GET", "POST"])
@login_required
def servers_edit(server_id: int):
    row = get_server(server_id)
    if row is None:
        flash("Server not found.", "warning")
        return redirect(url_for("main.servers_list"))
    error = None
    form = {
        "name": row["name"],
        "host": row["host"],
        "ssh_user": row["ssh_user"],
        "auth_type": row["auth_type"],
        "key_path": row["key_path"] or "",
        "password": "",
    }
    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            error = "Invalid form token."
        else:
            form = {
                "name": (request.form.get("name") or "").strip(),
                "host": (request.form.get("host") or "").strip(),
                "ssh_user": (request.form.get("ssh_user") or "").strip(),
                "auth_type": (request.form.get("auth_type") or "key").strip(),
                "key_path": (request.form.get("key_path") or "").strip(),
                "password": request.form.get("password") or "",
            }
            if not form["name"] or not form["host"] or not form["ssh_user"]:
                error = "Name, host, and SSH user are required."
            elif not validate_host(form["host"]):
                error = "Host must be a valid hostname or IPv4 address."
            elif form["auth_type"] not in {"key", "password"}:
                error = "Invalid auth type."
            else:
                password = form["password"] if form["auth_type"] == "password" else None
                if form["auth_type"] == "password" and not password:
                    password = row["password"]
                update_server(
                    server_id,
                    name=form["name"],
                    host=form["host"],
                    ssh_user=form["ssh_user"],
                    auth_type=form["auth_type"],
                    key_path=form["key_path"] or None,
                    password=password,
                )
                flash("Server updated.", "success")
                return redirect(url_for("main.servers_list"))
    return render_template(
        "server_form.html",
        title="Edit server",
        form=form,
        error=error,
        csrf_token=issue_csrf_token(),
        action=url_for("main.servers_edit", server_id=server_id),
    )


@bp.post("/servers/<int:server_id>/delete")
@login_required
def servers_delete(server_id: int):
    if not validate_csrf(request.form.get("csrf_token")):
        flash("Invalid form token.", "warning")
        return redirect(url_for("main.servers_list"))
    if get_server(server_id) is None:
        flash("Server not found.", "warning")
        return redirect(url_for("main.servers_list"))
    delete_server(server_id)
    flash("Server deleted.", "info")
    return redirect(url_for("main.servers_list"))


@bp.app_context_processor
def inject_auth():
    return {
        "current_username": session.get("username"),
        "csrf_token": session.get("csrf_token") or issue_csrf_token(),
    }
