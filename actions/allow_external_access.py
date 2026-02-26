import json
import os

from mcstatus import JavaServer

try:
    from discord_notify import send_discord_notification
    from opnsense_firewall import enable_rule
except ModuleNotFoundError:
    from actions.discord_notify import send_discord_notification
    from actions.opnsense_firewall import enable_rule


def _read_server_target():
    server_properties_path = "/opt/minecraft/server.properties"
    host = "127.0.0.1"
    port = 25565

    if not os.path.exists(server_properties_path):
        return host, port

    try:
        with open(server_properties_path, "r", encoding="utf-8") as properties_file:
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
                        pass
                elif key == "server-ip" and value:
                    host = value
    except Exception:
        return host, port

    return host, port


def _minecraft_is_reachable():
    host, port = _read_server_target()
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        server.status()
        return True
    except Exception:
        return False


def allow_external_access():
    if not _minecraft_is_reachable():
        send_discord_notification(
            "Firewall enable",
            success=False,
            detail="Minecraft server not reachable yet",
        )
        return False, "Minecraft server is not yet reachable. Start the server and wait until it is fully up before enabling external access."

    success, message = enable_rule()
    if not success:
        send_discord_notification(
            "Firewall enable",
            success=False,
            detail=message,
        )
        return False, message

    send_discord_notification(
        "Firewall rule enabled",
        success=True,
        detail="External access allowed",
    )

    return True, "External access enabled on OPNsense firewall rule"


if __name__ == "__main__":
    success, message = allow_external_access()
    print(json.dumps({"success": success}))
