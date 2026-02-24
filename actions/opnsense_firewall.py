import base64
import json
import os
import ssl
import urllib.error
import urllib.request


def load_opnsense_config():
    url = os.getenv("OPNSENSE_URL", "").strip().rstrip("/")
    api_key = os.getenv("OPNSENSE_API_KEY", "").strip()
    api_secret = os.getenv("OPNSENSE_API_SECRET", "").strip()
    rule_uuid = os.getenv("OPNSENSE_RULE_UUID", "").strip()

    missing = []
    if not url:
        missing.append("OPNSENSE_URL")
    if not api_key:
        missing.append("OPNSENSE_API_KEY")
    if not api_secret:
        missing.append("OPNSENSE_API_SECRET")
    if not rule_uuid:
        missing.append("OPNSENSE_RULE_UUID")

    if missing:
        return None, f"Missing required OPNsense environment variables: {', '.join(missing)}"

    verify_tls = os.getenv("OPNSENSE_VERIFY_TLS", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return {
        "url": url,
        "api_key": api_key,
        "api_secret": api_secret,
        "rule_uuid": rule_uuid,
        "verify_tls": verify_tls,
    }, None


def _opnsense_request(config, path, payload=None):
    endpoint = f"{config['url']}{path}"
    auth_raw = f"{config['api_key']}:{config['api_secret']}".encode("utf-8")
    auth_value = base64.b64encode(auth_raw).decode("ascii")

    headers = {
        "Authorization": f"Basic {auth_value}",
    }

    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(endpoint, data=body, method="POST", headers=headers)

    ssl_context = None
    if not config["verify_tls"]:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(request, context=ssl_context, timeout=20) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            if not response_text.strip():
                return True, None
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                return True, None

            result = response_json.get("result")
            if result == "failed":
                message = response_json.get("message") or response_json.get("validations") or "OPNsense request failed"
                return False, str(message)
            return True, None
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
            if error_body:
                return False, f"HTTP {exc.code} from OPNsense API: {error_body}"
        except Exception:
            pass
        return False, f"HTTP {exc.code} from OPNsense API"
    except urllib.error.URLError as exc:
        return False, f"Failed to reach OPNsense API: {exc.reason}"
    except Exception as exc:
        return False, f"Unexpected OPNsense API error: {exc}"


def set_rule_enabled(enabled):
    config, config_error = load_opnsense_config()
    if config_error:
        return False, config_error

    enabled_value = "1" if enabled else "0"
    set_rule_path = f"/api/firewall/filter/setRule/{config['rule_uuid']}"
    set_rule_payload = {"rule": {"enabled": enabled_value}}

    ok, err = _opnsense_request(config, set_rule_path, set_rule_payload)
    if not ok:
        return False, f"Failed to set firewall rule enabled={enabled_value}: {err}"

    ok, err = _opnsense_request(config, "/api/firewall/filter/apply")
    if not ok:
        return False, f"Failed to apply firewall rules: {err}"

    return True, "Firewall rule updated and applied successfully"


def enable_rule():
    return set_rule_enabled(True)


def disable_rule():
    return set_rule_enabled(False)


def _extract_enabled_value(payload):
    if isinstance(payload, dict):
        if "enabled" in payload:
            return payload.get("enabled")
        for value in payload.values():
            extracted = _extract_enabled_value(value)
            if extracted is not None:
                return extracted
    elif isinstance(payload, list):
        for item in payload:
            extracted = _extract_enabled_value(item)
            if extracted is not None:
                return extracted
    return None


def get_rule_enabled():
    config, config_error = load_opnsense_config()
    if config_error:
        return None, config_error

    get_rule_path = f"/api/firewall/filter/getRule/{config['rule_uuid']}"
    endpoint = f"{config['url']}{get_rule_path}"
    auth_raw = f"{config['api_key']}:{config['api_secret']}".encode("utf-8")
    auth_value = base64.b64encode(auth_raw).decode("ascii")

    request = urllib.request.Request(
        endpoint,
        method="POST",
        headers={"Authorization": f"Basic {auth_value}"},
    )

    ssl_context = None
    if not config["verify_tls"]:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(request, context=ssl_context, timeout=20) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            if not response_text.strip():
                return None, "OPNsense returned an empty rule response"

            response_json = json.loads(response_text)
            enabled_value = _extract_enabled_value(response_json)
            if enabled_value is None:
                return None, "Could not determine firewall rule enabled state from OPNsense response"

            enabled_normalized = str(enabled_value).strip().lower()
            if enabled_normalized in {"1", "true", "yes", "on"}:
                return True, None
            if enabled_normalized in {"0", "false", "no", "off"}:
                return False, None

            return None, f"Unrecognized firewall rule enabled value: {enabled_value}"
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
            if error_body:
                return None, f"HTTP {exc.code} from OPNsense API: {error_body}"
        except Exception:
            pass
        return None, f"HTTP {exc.code} from OPNsense API"
    except urllib.error.URLError as exc:
        return None, f"Failed to reach OPNsense API: {exc.reason}"
    except json.JSONDecodeError:
        return None, "OPNsense returned invalid JSON for rule status"
    except Exception as exc:
        return None, f"Unexpected OPNsense API error: {exc}"
