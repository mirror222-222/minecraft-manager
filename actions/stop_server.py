import subprocess
import json
import os
import sys
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from discord_notify import send_discord_notification
from opnsense_firewall import disable_rule

IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry, file=sys.stderr)

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
            send_discord_notification(
                "Minecraft server stop",
                success=False,
                detail=" | ".join(errors),
            )
            return False, " | ".join(errors)

        send_discord_notification(
            "Minecraft server stopped",
            success=True,
            detail="Firewall rule disabled",
        )
        return True, "Server stopped and firewall rule disabled"
    except Exception as e:
        log_error("stop_server exception", e)
        send_discord_notification(
            "Minecraft server stop",
            success=False,
            detail=str(e),
        )
        return False, str(e)

if __name__ == "__main__":
    success, msg = stop_server()
    print(json.dumps({"success": success, "message": msg}))
