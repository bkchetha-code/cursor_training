"""Demo Monitoring Infrastructure — Flask application factory."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parent.parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )

    app.config.from_mapping(
        # Security: override in production-like demos via FLASK_SECRET_KEY
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            str(ROOT / "demo_monitoring.db"),
        ),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin123"),
        SESSION_IDLE_SECONDS=int(os.environ.get("SESSION_IDLE_SECONDS", "1800")),
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config is not None:
        app.config.update(test_config)

    from app.db import close_db, init_db

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    from app.routes import bp

    app.register_blueprint(bp)
    return app
