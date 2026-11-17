"""HTTP routes — auth + read-only UI shell for the demo."""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.auth import (
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
from app.db import get_user_by_username

bp = Blueprint("main", __name__)


@bp.before_app_request
def enforce_idle_timeout():
    """Expire idle sessions globally; keep login/static usable."""
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
    """Landing page — branding and placeholder for monitoring views."""
    return render_template("home.html")


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
            # Security: never log password values
            user = get_user_by_username(username)
            if user is None or not verify_password(user["password_hash"], password):
                error = "Invalid username or password."
            else:
                login_user(user["id"], user["username"])
                issue_csrf_token()  # rotate after login
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


@bp.app_context_processor
def inject_auth():
    return {
        "current_username": session.get("username"),
        "csrf_token": session.get("csrf_token") or issue_csrf_token(),
    }
