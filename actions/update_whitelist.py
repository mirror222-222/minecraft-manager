
import subprocess
import json
import os
from datetime import datetime
import sys

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    print(entry)

def update_whitelist(data):
    try:
        server_dir = "/opt/minecraft"
        whitelist_path = os.path.join(server_dir, 'whitelist.json')
        # Load current whitelist
        if os.path.exists(whitelist_path):
            with open(whitelist_path, 'r') as f:
                current_whitelist = json.load(f)
        else:
            current_whitelist = []
        # Merge new entries with existing whitelist
        # Assume whitelist is a list of dicts with 'uuid' or 'name' as unique key
        def get_key(entry):
            return entry.get('uuid') or entry.get('name')
        existing_keys = {get_key(entry) for entry in current_whitelist}
        merged_whitelist = current_whitelist.copy()
        for entry in data:
            key = get_key(entry)
            if key not in existing_keys:
                merged_whitelist.append(entry)
                existing_keys.add(key)
        # Save merged whitelist
        with open(whitelist_path, 'w') as f:
            json.dump(merged_whitelist, f, indent=2)
        stop = subprocess.run(["systemctl", "stop", "minecraft"], capture_output=True, text=True)
        if stop.returncode != 0:
            msg = f"Failed to stop server: {stop.stderr}"
            log_error(msg)
            return False, msg
        start = subprocess.run(["systemctl", "start", "minecraft"], capture_output=True, text=True)
        if start.returncode != 0:
            msg = f"Failed to start server: {start.stderr}"
            log_error(msg)
            return False, msg
        return True, "Whitelist updated and server restarted"
    except Exception as e:
        log_error("update_whitelist exception", e)
        return False, str(e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = json.load(sys.stdin)
    success, msg = update_whitelist(data)
    print(json.dumps({"success": success, "message": msg}))
