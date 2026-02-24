import json

from opnsense_firewall import get_rule_enabled


def get_external_access_status():
    enabled, error = get_rule_enabled()
    if error:
        return {
            "configured": False,
            "enabled": None,
            "label": "External access status unavailable",
            "message": error,
        }

    if enabled:
        return {
            "configured": True,
            "enabled": True,
            "label": "External access: Enabled",
            "message": "OPNsense firewall rule is enabled",
        }

    return {
        "configured": True,
        "enabled": False,
        "label": "External access: Disabled",
        "message": "OPNsense firewall rule is disabled",
    }


if __name__ == "__main__":
    print(json.dumps(get_external_access_status()))
