import json

from opnsense_firewall import disable_rule


def disable_external_access():
    success, message = disable_rule()
    if not success:
        return False, message

    return True, "External access disabled on OPNsense firewall rule"


if __name__ == "__main__":
    success, message = disable_external_access()
    print(json.dumps({"success": success, "message": message}))
