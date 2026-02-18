import subprocess
import json
import os
from datetime import datetime

IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry)

def stop_server():
    try:
        if os.path.exists(IDLE_NOTICE_PATH):
            os.remove(IDLE_NOTICE_PATH)
        # If you need to reference files, use /opt/minecraft as the server directory
        stop = subprocess.run(["systemctl", "stop", "minecraft"], capture_output=True, text=True)
        if stop.returncode != 0:
            msg = f"Failed to stop server: {stop.stderr}"
            log_error(msg)
            return False, msg
        return True, "Server stopped"
    except Exception as e:
        log_error("stop_server exception", e)
        return False, str(e)

if __name__ == "__main__":
    success, msg = stop_server()
    print(json.dumps({"success": success, "message": msg}))
