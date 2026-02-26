import json

try:
    from discord_notify import send_discord_notification
    from opnsense_firewall import disable_rule
    from redaction import redact_sensitive_text
except ModuleNotFoundError:
    from actions.discord_notify import send_discord_notification
    from actions.opnsense_firewall import disable_rule
    from actions.redaction import redact_sensitive_text


def disable_external_access():
    success, message = disable_rule()
    if not success:
        send_discord_notification(
            "Firewall disable",
            success=False,
            detail=message,
        )
        return False, message

    send_discord_notification(
        "Firewall rule disabled",
        success=True,
        detail="External access blocked",
    )

    return True, "External access disabled on OPNsense firewall rule"


if __name__ == "__main__":
    success, message = disable_external_access()
    safe_message = redact_sensitive_text(message)
    print(json.dumps({"success": success, "message": safe_message}))
