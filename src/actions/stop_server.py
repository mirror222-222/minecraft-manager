import subprocess
import json
from datetime import datetime

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry)

def stop_server():
    try:
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
