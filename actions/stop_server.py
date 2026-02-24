import subprocess
import json
import os
from datetime import datetime

from opnsense_firewall import disable_rule

IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry)

def stop_server():
    errors = []
    try:
        if os.path.exists(IDLE_NOTICE_PATH):
            os.remove(IDLE_NOTICE_PATH)

        stop = subprocess.run(["systemctl", "stop", "minecraft"], capture_output=True, text=True)
        if stop.returncode != 0:
            msg = f"Failed to stop server: {stop.stderr}"
            log_error(msg)
            errors.append(msg)

        disable_ok, disable_msg = disable_rule()
        if not disable_ok:
            log_error(f"Failed to disable OPNsense firewall rule: {disable_msg}")
            errors.append(f"Failed to disable OPNsense firewall rule: {disable_msg}")

        if errors:
            return False, " | ".join(errors)
        return True, "Server stopped and firewall rule disabled"
    except Exception as e:
        log_error("stop_server exception", e)
        return False, str(e)

if __name__ == "__main__":
    success, msg = stop_server()
    print(json.dumps({"success": success, "message": msg}))
