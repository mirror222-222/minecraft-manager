
import subprocess
import json
import os
from datetime import datetime
import sys
from redaction import redact_sensitive_text

IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {redact_sensitive_text(message)}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {redact_sensitive_text(exc)}"
    print(entry)

def update_whitelist(data):
    try:
        server_dir = "/opt/minecraft"
        whitelist_path = os.path.join(server_dir, 'whitelist.json')
        if os.path.exists(IDLE_NOTICE_PATH):
            os.remove(IDLE_NOTICE_PATH)
        # Always overwrite the whitelist file with the new data
        with open(whitelist_path, 'w') as f:
            json.dump(data, f, indent=2)
        stop = subprocess.run(["systemctl", "stop", "minecraft"], capture_output=True, text=True)
        if stop.returncode != 0:
            msg = redact_sensitive_text(f"Failed to stop server: {stop.stderr}")
            log_error(msg)
            return False, msg
        start = subprocess.run(["systemctl", "start", "minecraft"], capture_output=True, text=True)
        if start.returncode != 0:
            msg = redact_sensitive_text(f"Failed to start server: {start.stderr}")
            log_error(msg)
            return False, msg
        return True, "Whitelist updated and server restarted"
    except Exception as e:
        log_error("update_whitelist exception", e)
        return False, redact_sensitive_text(str(e))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = json.load(sys.stdin)
    success, msg = update_whitelist(data)
    print(json.dumps({"success": success, "message": redact_sensitive_text(msg)}))
