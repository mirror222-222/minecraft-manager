
from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading
import time
import os
import json
import subprocess
from collections import deque
from datetime import datetime

app = Flask(__name__)

# Globals for idle shutdown
last_user_activity = time.time()
idle_minutes = 30
user_check_interval = 60  # seconds
server_running = False
error_log = deque(maxlen=100)

def log_error(message, exc=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {message}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {exc}"
    error_log.append(entry)

def check_users_periodically():
    global last_user_activity, server_running
    while True:
        if server_running:
            user_count = get_connected_users()
            if user_count > 0:
                last_user_activity = time.time()
            elif time.time() - last_user_activity > idle_minutes * 60:
                stop_server()
                server_running = False
        time.sleep(user_check_interval)

def get_connected_users():
    # TODO: Implement logic to check connected users (e.g., query server or parse logs)
    return 0

def start_server():
    global server_running
    try:
        # 1. Run apt update
        apt = subprocess.run(["apt", "update"], capture_output=True, text=True)
        if apt.returncode != 0:
            msg = f"apt update failed: {apt.stderr}"
            log_error(msg)
            return False, msg

        # 2. Check/download Minecraft server jar (placeholder logic)
        # TODO: Replace with real version check and download
        server_jar = "server.jar"
        if not os.path.exists(server_jar):
            # Download latest server jar (placeholder URL)
            url = "https://launcher.mojang.com/v1/objects/placeholder/server.jar"
            dl = subprocess.run(["wget", "-O", server_jar, url], capture_output=True, text=True)
            if dl.returncode != 0:
                msg = f"Download failed: {dl.stderr}"
                log_error(msg)
                return False, msg

        # 3. Ensure eula.txt exists and is set to eula=true
        with open("eula.txt", "w") as f:
            f.write("eula=true\n")

        # 4. Ensure allowlist-only mode (server.properties)
        props = "server.properties"
        if os.path.exists(props):
            with open(props) as f:
                lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if line.startswith("enforce-whitelist"):
                    lines[i] = "enforce-whitelist=true\n"
                    found = True
            if not found:
                lines.append("enforce-whitelist=true\n")
            with open(props, "w") as f:
                f.writelines(lines)
        else:
            with open(props, "w") as f:
                f.write("enforce-whitelist=true\n")

        # 5. Start Minecraft server service (systemd)
        start = subprocess.run(["systemctl", "start", "minecraft"], capture_output=True, text=True)
        if start.returncode != 0:
            msg = f"Failed to start server: {start.stderr}"
            log_error(msg)
            return False, msg

        server_running = True
        return True, "Server started"
    except Exception as e:
        log_error("start_server exception", e)
        return False, str(e)

def stop_server():
    global server_running
    try:
        stop = subprocess.run(["systemctl", "stop", "minecraft"], capture_output=True, text=True)
        if stop.returncode != 0:
            msg = f"Failed to stop server: {stop.stderr}"
            log_error(msg)
            return False, msg
        server_running = False
        return True, "Server stopped"
    except Exception as e:
        log_error("stop_server exception", e)
        return False, str(e)

def update_whitelist(data):
    try:
        with open('whitelist.json', 'w') as f:
            json.dump(data, f, indent=2)
        # Restart Minecraft server to apply whitelist changes
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

@app.route("/")
def index():
    # TODO: Render main manager page
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    success, msg = start_server()
    return jsonify({"success": success, "message": msg})

@app.route("/stop", methods=["POST"])
def stop():
    success, msg = stop_server()
    return jsonify({"success": success, "message": msg})

@app.route("/whitelist", methods=["GET", "POST"])
def whitelist():
    if request.method == "POST":
        data = request.get_json()
        success, msg = update_whitelist(data)
        return jsonify({"success": success, "message": msg})
    else:
        try:
            with open('whitelist.json') as f:
                data = json.load(f)
        except Exception:
            log_error("Unable to read whitelist.json")
            data = []
        return jsonify(data)

@app.route("/errors", methods=["GET"])
def errors():
    return jsonify(list(error_log))

@app.route("/errors/clear", methods=["POST"])
def clear_errors():
    error_log.clear()
    return jsonify({"success": True, "message": "Error log cleared"})

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    log_error("Unhandled application error", e)
    return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route("/status")
def status():
    # TODO: Return server status and user count
    return jsonify({"running": server_running, "users": get_connected_users()})

if __name__ == "__main__":
    # Start background thread for user check
    t = threading.Thread(target=check_users_periodically, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
