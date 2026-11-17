"""Local entrypoint — binds on all interfaces for multi-host demo access."""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5243"))
    # Demo: 0.0.0.0 so other hosts on the network can reach the UI
    app.run(host=host, port=port, debug=True)
