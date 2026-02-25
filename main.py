
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

import threading, time, os, json, subprocess, sys
from collections import deque
from datetime import datetime, UTC
from mcstatus import JavaServer
from actions.redaction import redact_sensitive_text

app = Flask(__name__, template_folder="templates", static_folder="static")
error_log = deque(maxlen=100)
IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"

def log_error(message, exc=None):
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {redact_sensitive_text(message)}"
    if exc is not None:
        entry += f" | {type(exc).__name__}: {redact_sensitive_text(exc)}"
    error_log.append(entry)


def _safe_message(message):
    return redact_sensitive_text(message)


def _public_external_access_payload(external_access):
    if not isinstance(external_access, dict):
        return {
            "configured": False,
            "enabled": None,
            "label": "External access status unavailable",
        }

    return {
        "configured": external_access.get("configured", False),
        "enabled": external_access.get("enabled", None),
        "label": external_access.get("label", "External access status unavailable"),
    }

def get_connected_users():
    try:
        # Default to localhost and port 25565, adjust if needed
        server = JavaServer.lookup("localhost:25565")
        status = server.status()
        return status.players.online
    except Exception as e:
        log_error(f"mcstatus error: {e}")
        return 0

def start_server():
    try:
        result = subprocess.run([sys.executable, os.path.abspath("actions/start_server.py")], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            logs = output.get("log", [])
            for log_entry in logs:
                error_log.append(_safe_message(log_entry))
            return output.get("success", False), _safe_message(output.get("message", ""))
        else:
            log_error(f"start_server.py failed: {result.stderr}")
            return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("start_server exception", e)
        return False, _safe_message(str(e))

def stop_server():
    try:
        result = subprocess.run([sys.executable, os.path.abspath("actions/stop_server.py")], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            success = output.get("success", False)
            message = output.get("message", "")
            if not success and message:
                log_error(f"stop_server action failed: {message}")
            return success, _safe_message(message)
        else:
            log_error(f"stop_server.py failed: {result.stderr}")
            return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("stop_server exception", e)
        return False, _safe_message(str(e))


def allow_external_access():
    try:
        result = subprocess.run(
            [sys.executable, os.path.abspath("actions/allow_external_access.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            success = output.get("success", False)
            message = output.get("message", "")
            if not success and message:
                log_error(f"allow_external_access action failed: {message}")
            return success, _safe_message(message)
        log_error(f"allow_external_access.py failed: {result.stderr}")
        return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("allow_external_access exception", e)
        return False, _safe_message(str(e))


def disable_external_access():
    try:
        result = subprocess.run(
            [sys.executable, os.path.abspath("actions/disable_external_access.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            success = output.get("success", False)
            message = output.get("message", "")
            if not success and message:
                log_error(f"disable_external_access action failed: {message}")
            return success, _safe_message(message)
        log_error(f"disable_external_access.py failed: {result.stderr}")
        return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("disable_external_access exception", e)
        return False, _safe_message(str(e))


def test_discord_notification():
    try:
        result = subprocess.run(
            [sys.executable, os.path.abspath("actions/test_discord_notification.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = json.loads(result.stdout)
            success = output.get("success", False)
            message = output.get("message", "")
            if not success and message:
                log_error(f"test_discord_notification action failed: {message}")
            return success, _safe_message(message)
        log_error(f"test_discord_notification.py failed: {result.stderr}")
        return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("test_discord_notification exception", e)
        return False, _safe_message(str(e))


def get_external_access_status():
    default_status = {
        "configured": False,
        "enabled": None,
        "label": "External access status unavailable",
        "message": "Configure OPNsense environment variables to show status",
    }

    try:
        result = subprocess.run(
            [sys.executable, os.path.abspath("actions/get_external_access_status.py")],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log_error(f"get_external_access_status.py failed: {result.stderr}")
            return default_status

        output = json.loads(result.stdout)
        if isinstance(output, dict):
            return _public_external_access_payload({
                "configured": output.get("configured", False),
                "enabled": output.get("enabled", None),
                "label": output.get("label", default_status["label"]),
                "message": output.get("message", default_status["message"]),
            })
        return _public_external_access_payload(default_status)
    except Exception as e:
        log_error("get_external_access_status exception", e)
        return default_status

def update_whitelist(data):
    try:
        result = subprocess.run([
            sys.executable, os.path.abspath("actions/update_whitelist.py"), json.dumps(data)
        ], capture_output=True, text=True)
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output.get("success", False), output.get("message", "")
        else:
            log_error(f"update_whitelist.py failed: {result.stderr}")
            return False, _safe_message(result.stderr)
    except Exception as e:
        log_error("update_whitelist exception", e)
        return False, _safe_message(str(e))

def get_whitelist_json():
    whitelist_path = "/opt/minecraft/whitelist.json"
    try:
        with open(whitelist_path) as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        log_error(f"Failed to load whitelist.json: {e}")
        return "[]"

def get_error_log():
    return list(error_log)


def get_idle_shutdown_notice_message():
    if not os.path.exists(IDLE_NOTICE_PATH):
        return None
    try:
        with open(IDLE_NOTICE_PATH, "r", encoding="utf-8") as notice_file:
            payload = json.load(notice_file)
        if payload.get("reason") != "inactivity":
            return None
        timeout_minutes = payload.get("idle_timeout_minutes", 30)
        stopped_at_utc = payload.get("stopped_at_utc")
        if stopped_at_utc:
            return f"Server stopped due to inactivity ({timeout_minutes} minutes with no users). Time: {stopped_at_utc}"
        return f"Server stopped due to inactivity ({timeout_minutes} minutes with no users)."
    except Exception as e:
        log_error("Failed to load idle shutdown notice", e)
        return None

def get_status_message():
    try:
        status = subprocess.run(["systemctl", "is-active", "minecraft"], capture_output=True, text=True)
        running = status.stdout.strip() == "active"
    except Exception:
        running = False
    users = get_connected_users()
    if running:
        return f"Server running. Users: {users}", False, True
    else:
        idle_notice = get_idle_shutdown_notice_message()
        if idle_notice:
            return idle_notice, False, False
        return "Server stopped.", False, False

@app.route("/", methods=["GET"])
def index():
    status_message, status_error, server_running = get_status_message()
    external_access = get_external_access_status()
    return render_template(
        "index.html",
        status_message=status_message,
        status_error=status_error,
        server_running=server_running,
        external_access=external_access,
        whitelist_json=get_whitelist_json(),
        error_log=get_error_log()
    )

@app.route("/start", methods=["POST"])
def start():
    success, msg = start_server()
    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop():
    success, msg = stop_server()
    return redirect(url_for("index"))


@app.route("/allow-external-access", methods=["POST"])
def allow_external_access_route():
    success, msg = allow_external_access()
    return redirect(url_for("index"))


@app.route("/disable-external-access", methods=["POST"])
def disable_external_access_route():
    success, msg = disable_external_access()
    return redirect(url_for("index"))


@app.route("/test-discord", methods=["POST"])
def test_discord_route():
    success, msg = test_discord_notification()
    return redirect(url_for("index"))

@app.route("/whitelist", methods=["POST"])
def whitelist():
    try:
        data = json.loads(request.form["whitelistBox"])
    except Exception as e:
        log_error(f"Invalid JSON in whitelist: {e}")
        return redirect(url_for("index"))
    success, msg = update_whitelist(data)
    time.sleep(0.1)  # Ensure file write completes
    return redirect(url_for("index"))

@app.route("/errors/clear", methods=["POST"])
def clear_errors():
    error_log.clear()
    return redirect(url_for("index"))

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    log_error("Unhandled application error", e)
    return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route("/status")
def status():
    status_message, status_error, server_running = get_status_message()
    external_access = get_external_access_status()
    return jsonify(
        {
            "running": server_running,
            "users": get_connected_users(),
            "status_message": status_message,
            "status_error": status_error,
            "external_access": external_access,
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
