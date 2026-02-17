# main.py moved to project root

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
    try:
        result = subprocess.run(["python3", "src/actions/start_server.py"], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get("success", False), output.get("message", "")
        else:
            log_error(f"start_server.py failed: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        log_error("start_server exception", e)
        return False, str(e)


def stop_server():
    try:
        result = subprocess.run(["python3", "src/actions/stop_server.py"], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get("success", False), output.get("message", "")
        else:
            log_error(f"stop_server.py failed: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        log_error("stop_server exception", e)
        return False, str(e)


def update_whitelist(data):
    try:
        result = subprocess.run([
            "python3", "src/actions/update_whitelist.py", json.dumps(data)
        ], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get("success", False), output.get("message", "")
        else:
            log_error(f"update_whitelist.py failed: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        log_error("update_whitelist exception", e)
        return False, str(e)


def get_whitelist_json():
    try:
        with open('/opt/minecraft/whitelist.json') as f:
            data = json.load(f)
        print("DEBUG: Loaded whitelist.json:", data)
        return json.dumps(data, indent=2)
    except Exception as e:
        log_error(f"Failed to load whitelist.json: {e}")
        print(f"DEBUG: Failed to load whitelist.json: {e}")
        try:
            with open('/opt/minecraft/whitelist.json') as f:
                raw = f.read()
            print("DEBUG: Raw whitelist.json:", raw)
            return raw
        except Exception as e2:
            print(f"DEBUG: Could not read whitelist.json: {e2}")
            return "[]"

def get_error_log():
    return list(error_log)

def get_status_message():
    running = server_running
    users = get_connected_users()
    if running:
        return f"Server running. Users: {users}", False
    else:
        return "Server stopped.", False

@app.route("/", methods=["GET"])
def index():
    status_message, status_error = get_status_message()
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        whitelist_json=get_whitelist_json(),
        error_log=get_error_log()
    )


@app.route("/start", methods=["POST"])
def start():
    success, msg = start_server()
    status_message = msg
    status_error = not success
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        whitelist_json=get_whitelist_json(),
        error_log=get_error_log()
    )


@app.route("/stop", methods=["POST"])
def stop():
    success, msg = stop_server()
    status_message = msg
    status_error = not success
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        whitelist_json=get_whitelist_json(),
        error_log=get_error_log()
    )


@app.route("/whitelist", methods=["POST"])
def whitelist():
    try:
        data = json.loads(request.form["whitelistBox"])
        print("DEBUG: Received whitelistBox:", data)
    except Exception as e:
        log_error(f"Invalid JSON in whitelist: {e}")
        print(f"DEBUG: Invalid JSON in whitelist: {e}")
        status_message = "Invalid JSON in whitelist."
        status_error = True
        return render_template(
            "index.html",
            status_message=status_message,
            status_error=status_error,
            whitelist_json=request.form["whitelistBox"],
            error_log=get_error_log()
        )
    print("DEBUG: Calling update_whitelist with:", data)
    success, msg = update_whitelist(data)
    print(f"DEBUG: update_whitelist returned success={success}, msg={msg}")
    status_message = msg
    status_error = not success
    # After saving, reload from disk to display the actual saved values
    import time
    time.sleep(0.1)  # Small delay to ensure file write completes
    whitelist_contents = get_whitelist_json()
    print("DEBUG: get_whitelist_json returned:", whitelist_contents)
    # If whitelist_contents is not valid JSON, show an error
    try:
        json.loads(whitelist_contents)
    except Exception as e:
        log_error(f"Whitelist file invalid after save: {e}")
        print(f"DEBUG: Whitelist file invalid after save: {e}")
        status_message += f" | Whitelist file invalid: {e}"
        status_error = True
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        whitelist_json=whitelist_contents,
        error_log=get_error_log()
    )


@app.route("/errors/clear", methods=["POST"])
def clear_errors():
    error_log.clear()
    status_message = "Error log cleared"
    status_error = False
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        whitelist_json=get_whitelist_json(),
        error_log=get_error_log()
    )

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
