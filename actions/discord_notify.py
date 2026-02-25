import json
import os
import ssl
import urllib.error
import urllib.request
from datetime import datetime, UTC


DISCORD_ENV_FILE_PATH = "/etc/minecraft-manager/discord.env"


def _strip_wrapping_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _read_env_file(path):
    env_values = {}
    if not os.path.exists(path):
        return env_values

    try:
        with open(path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                if not key:
                    continue

                env_values[key] = _strip_wrapping_quotes(value)
    except Exception:
        return {}

    return env_values


def _get_config_value(name, file_values):
    value = os.getenv(name)
    if value is not None and value.strip() != "":
        return value.strip()

    file_value = file_values.get(name)
    if file_value is None:
        return ""

    return file_value.strip()


def load_discord_config():
    env_file_values = _read_env_file(DISCORD_ENV_FILE_PATH)

    webhook_url = _get_config_value("DISCORD_WEBHOOK_URL", env_file_values)
    if not webhook_url:
        return None, "DISCORD_WEBHOOK_URL is not configured"

    verify_tls = _get_config_value("DISCORD_VERIFY_TLS", env_file_values).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return {
        "webhook_url": webhook_url,
        "username": _get_config_value("DISCORD_WEBHOOK_USERNAME", env_file_values),
        "avatar_url": _get_config_value("DISCORD_WEBHOOK_AVATAR_URL", env_file_values),
        "mention": _get_config_value("DISCORD_MENTION", env_file_values),
        "verify_tls": verify_tls,
    }, None


def _build_message(event_name, success, detail):
    icon = "✅" if success else "❌"
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    base = f"{icon} {event_name} ({timestamp})"
    if detail:
        return f"{base}\n{detail}"
    return base


def send_discord_notification(event_name, success=True, detail=""):
    config, config_error = load_discord_config()
    if config_error:
        return False, config_error

    content = _build_message(event_name=event_name, success=success, detail=detail)
    if config["mention"]:
        content = f"{config['mention']}\n{content}"

    payload = {"content": content}
    if config["username"]:
        payload["username"] = config["username"]
    if config["avatar_url"]:
        payload["avatar_url"] = config["avatar_url"]

    request = urllib.request.Request(
        config["webhook_url"],
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
    )

    ssl_context = None
    if not config["verify_tls"]:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(request, context=ssl_context, timeout=15):
            return True, "Discord notification sent"
    except urllib.error.HTTPError as exc:
        response_body = ""
        try:
            response_body = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            response_body = ""

        if response_body:
            try:
                payload = json.loads(response_body)
                message = payload.get("message")
                error_code = payload.get("code")
                if message and error_code is not None:
                    return False, f"Discord webhook HTTP error: {exc.code} ({message}, code={error_code})"
                if message:
                    return False, f"Discord webhook HTTP error: {exc.code} ({message})"
            except Exception:
                pass
            return False, f"Discord webhook HTTP error: {exc.code} ({response_body})"

        return False, f"Discord webhook HTTP error: {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"Discord webhook connection error: {exc.reason}"
    except Exception as exc:
        return False, f"Discord notification error: {exc}"
