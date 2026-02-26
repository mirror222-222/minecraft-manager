import os
import subprocess
import time
from datetime import datetime, UTC

from mcstatus import JavaServer
from redaction import redact_sensitive_text

try:
    from discord_notify import send_discord_notification
    from opnsense_firewall import disable_rule
except ModuleNotFoundError:
    from actions.discord_notify import send_discord_notification
    from actions.opnsense_firewall import disable_rule

CHECK_INTERVAL_SECONDS = 60
IDLE_TIMEOUT_MINUTES = 30
MINECRAFT_SERVICE_NAME = "minecraft"
SERVER_PROPERTIES_PATH = "/opt/minecraft/server.properties"
IDLE_NOTICE_PATH = "/opt/minecraft/idle_shutdown_notice.json"
DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 25565


def log(message: str) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {redact_sensitive_text(message)}", flush=True)


def read_server_target() -> tuple[str, int]:
    host = DEFAULT_SERVER_HOST
    port = DEFAULT_SERVER_PORT

    if not os.path.exists(SERVER_PROPERTIES_PATH):
        return host, port

    try:
        with open(SERVER_PROPERTIES_PATH, "r", encoding="utf-8") as properties_file:
            for raw_line in properties_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "server-port" and value:
                    try:
                        port = int(value)
                    except ValueError:
                        log(f"Invalid server-port in server.properties: {value}")
                elif key == "server-ip" and value:
                    host = value
    except Exception:
        log("Failed to parse server.properties")

    return host, port


def is_server_active() -> bool:
    result = subprocess.run(
        ["systemctl", "is-active", MINECRAFT_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "active"


def get_online_players(host: str, port: int) -> int | None:
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        status = server.status()
        return status.players.online
    except Exception:
        log("Failed to query online player count")
        return None


def stop_minecraft_server() -> bool:
    failed = False
    stop_failed = False
    firewall_failed = False

    result = subprocess.run(
        ["systemctl", "stop", MINECRAFT_SERVICE_NAME],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log(f"Failed to stop minecraft service (exit code {result.returncode})")
        failed = True
        stop_failed = True

    disable_ok, disable_message = disable_rule()
    if not disable_ok:
        log(f"Failed to disable OPNsense firewall rule: {disable_message}")
        failed = True
        firewall_failed = True

    if failed:
        detail_parts = []
        if stop_failed:
            detail_parts.append("Minecraft service stop failed")
        if firewall_failed:
            detail_parts.append("Firewall rule disable failed")
        send_discord_notification(
            "Idle timeout stop",
            success=False,
            detail=" | ".join(detail_parts),
        )
    else:
        send_discord_notification(
            "Minecraft server stopped (idle timeout)",
            success=True,
            detail="Firewall rule disabled",
        )

    return not failed


def write_idle_shutdown_notice() -> None:
    payload = {
        "reason": "inactivity",
        "idle_timeout_minutes": IDLE_TIMEOUT_MINUTES,
        "stopped_at_utc": datetime.now(UTC).isoformat(),
    }
    try:
        with open(IDLE_NOTICE_PATH, "w", encoding="utf-8") as notice_file:
            import json

            json.dump(payload, notice_file)
    except Exception:
        log("Failed to write idle shutdown notice")


def main() -> None:
    idle_minutes = 0
    log(
        "Minecraft idle monitor started "
        f"(timeout={IDLE_TIMEOUT_MINUTES} minutes, interval={CHECK_INTERVAL_SECONDS} seconds)."
    )

    while True:
        if not is_server_active():
            if idle_minutes != 0:
                log("Minecraft service is not active. Idle timer reset.")
            idle_minutes = 0
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        host, port = read_server_target()
        online_players = get_online_players(host, port)

        if online_players is None:
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        if online_players > 0:
            if idle_minutes != 0:
                log(f"Players online ({online_players}). Idle timer reset.")
            idle_minutes = 0
        else:
            idle_minutes += 1
            log(f"No players online. Idle minute {idle_minutes}/{IDLE_TIMEOUT_MINUTES}.")

            if idle_minutes >= IDLE_TIMEOUT_MINUTES:
                log("Idle timeout reached. Stopping minecraft service.")
                if stop_minecraft_server():
                    write_idle_shutdown_notice()
                    log("Minecraft service stopped due to inactivity.")
                idle_minutes = 0

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
