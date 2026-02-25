import json

from discord_notify import send_discord_notification


def test_discord_notification():
    success, message = send_discord_notification(
        "Discord integration test",
        success=True,
        detail="Minecraft Manager test notification",
    )
    if not success:
        return False, message
    return True, "Discord test notification sent"


if __name__ == "__main__":
    success, message = test_discord_notification()
    print(json.dumps({"success": success, "message": message}))
