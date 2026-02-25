import subprocess
import os
import datetime
import time
import json
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from discord_notify import send_discord_notification


log_messages = []
IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"
from datetime import datetime, UTC
def log_error(message, exc=None):
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    log_messages.append(entry)


def clear_idle_shutdown_notice():
    try:
        if os.path.exists(IDLE_NOTICE_PATH):
            os.remove(IDLE_NOTICE_PATH)
            log_messages.append("[INFO] Cleared idle shutdown notice.")
    except Exception as e:
        log_error("Failed to clear idle shutdown notice", e)


def _split_property_line(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None, None
    key, value = stripped.split("=", 1)
    return key.strip(), value.strip()


def _normalize_server_properties(lines, overrides):
    last_index_by_key = {}
    parsed_lines = []

    for index, line in enumerate(lines):
        key, _ = _split_property_line(line)
        parsed_lines.append((line, key))
        if key is not None:
            last_index_by_key[key] = index

    normalized_lines = []
    seen_override_keys = set()

    for index, (original_line, key) in enumerate(parsed_lines):
        if key is None:
            normalized_lines.append(original_line)
            continue

        if last_index_by_key.get(key) != index:
            continue

        if key in overrides:
            normalized_lines.append(f"{key}={overrides[key]}\n")
            seen_override_keys.add(key)
        else:
            normalized_lines.append(original_line)

    for override_key, override_value in overrides.items():
        if override_key not in seen_override_keys:
            normalized_lines.append(f"{override_key}={override_value}\n")

    return normalized_lines


def _ensure_server_properties(props_path):
    override_properties = {
        "enforce-whitelist": "true",
    }

    if os.path.exists(props_path):
        log_messages.append("[INFO] Normalizing server.properties and enforcing whitelist settings...")
        with open(props_path, "r", encoding="utf-8") as properties_file:
            lines = properties_file.readlines()
        normalized_lines = _normalize_server_properties(lines, override_properties)
    else:
        log_messages.append("[INFO] Creating server.properties with whitelist settings...")
        normalized_lines = [f"{key}={value}\n" for key, value in override_properties.items()]

    with open(props_path, "w", encoding="utf-8") as properties_file:
        properties_file.writelines(normalized_lines)

def start_server():
    try:
        server_dir = "/opt/minecraft"
        if not os.path.exists(server_dir):
            log_messages.append(f"[INFO] Creating server directory at {server_dir}")
            os.makedirs(server_dir, exist_ok=True)
        server_jar = os.path.join(server_dir, "server.jar")
        version_file = os.path.join(server_dir, "server.jar.version")
        import urllib.request
        log_messages.append("[INFO] Checking for latest Minecraft server version...")
        try:
            version_manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            with urllib.request.urlopen(version_manifest_url) as response:
                manifest = response.read().decode()
            manifest_json = json.loads(manifest)
            latest_release = manifest_json["latest"]["release"]
            log_messages.append(f"[INFO] Latest Minecraft release: {latest_release}")
            version_info = next(v for v in manifest_json["versions"] if v["id"] == latest_release)
            version_url = version_info["url"]
            with urllib.request.urlopen(version_url) as response:
                version_data = response.read().decode()
            version_json = json.loads(version_data)
            url = version_json["downloads"]["server"]["url"]
        except Exception as e:
            msg = f"Failed to fetch latest server JAR URL: {e}"
            log_error(msg)
            return False, msg

        need_download = False
        current_version = None
        if os.path.exists(server_jar) and os.path.exists(version_file):
            with open(version_file) as vf:
                current_version = vf.read().strip()
            if current_version != latest_release:
                log_messages.append(f"[INFO] Server out of date (current: {current_version}, latest: {latest_release}). Will update.")
                need_download = True
            else:
                log_messages.append(f"[INFO] Server is up to date (version: {current_version}).")
        else:
            log_messages.append("[INFO] No server.jar found. Will download latest.")
            need_download = True

        if need_download:
            log_messages.append(f"[INFO] Downloading Minecraft server {latest_release}...")
            dl = subprocess.run(["wget", "-O", server_jar, url], capture_output=True, text=True)
            if dl.returncode != 0:
                msg = f"Download failed: {dl.stderr}"
                log_error(msg)
                return False, msg
            with open(version_file, "w") as vf:
                vf.write(latest_release)
            log_messages.append(f"[INFO] Downloaded and updated to version {latest_release}.")
        log_messages.append("[INFO] Accepting EULA...")
        with open(os.path.join(server_dir, "eula.txt"), "w") as f:
            f.write("eula=true\n")
        props = os.path.join(server_dir, "server.properties")
        _ensure_server_properties(props)
        # Start the Minecraft server as a systemd service
        log_messages.append("[INFO] Starting Minecraft server via systemd service...")
        try:
            start = subprocess.run(["systemctl", "start", "minecraft"], capture_output=True, text=True)
            if start.returncode != 0:
                msg = f"Failed to start server: {start.stderr}"
                log_error(msg)
                log_messages.append(f"[ERROR] {msg}")
                discord_ok, discord_msg = send_discord_notification(
                    "Minecraft server start",
                    success=False,
                    detail=msg,
                )
                if not discord_ok:
                    log_messages.append(f"[WARN] Discord notification failed: {discord_msg}")
                return False, msg
            clear_idle_shutdown_notice()
            # Get server IP and port from server.properties
            props_path = os.path.join(server_dir, "server.properties")
            server_ip = "0.0.0.0"
            server_port = "25565"
            if os.path.exists(props_path):
                with open(props_path) as f:
                    for line in f:
                        if line.startswith("server-ip"):
                            server_ip = line.split("=")[1].strip() or "0.0.0.0"
                        if line.startswith("server-port"):
                            server_port = line.split("=")[1].strip() or "25565"
            log_messages.append(f"[SUCCESS] Minecraft server started (systemd service)")
            log_messages.append(f"[INFO] Minecraft server listening on {server_ip}:{server_port}")
            # Stub: user count (real implementation would parse logs or query server)
            user_count = 0
            log_messages.append(f"[INFO] Users online: {user_count}")
            discord_ok, discord_msg = send_discord_notification(
                "Minecraft server started",
                success=True,
                detail=f"Listening on {server_ip}:{server_port}",
            )
            if not discord_ok:
                log_messages.append(f"[WARN] Discord notification failed: {discord_msg}")
            return True, f"Server started (systemd service) at {server_ip}:{server_port} with {user_count} users online"
        except Exception as e:
            msg = f"Failed to start server: {e}"
            log_error(msg)
            log_messages.append(f"[ERROR] {msg}")
            discord_ok, discord_msg = send_discord_notification(
                "Minecraft server start",
                success=False,
                detail=msg,
            )
            if not discord_ok:
                log_messages.append(f"[WARN] Discord notification failed: {discord_msg}")
            return False, msg
    except Exception as e:
        log_error("start_server exception", e)
        return False, str(e)

if __name__ == "__main__":
    success, msg = start_server()
    print(json.dumps({"success": success, "message": msg, "log": log_messages}))
