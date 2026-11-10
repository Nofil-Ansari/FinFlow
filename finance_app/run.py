import os
from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    socketio.run(app, debug=debug_mode, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
