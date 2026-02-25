import re


_REPLACEMENTS = [
    (
        re.compile(r"(https?://(?:discord\.com|discordapp\.com)/api/webhooks/)[^\s\"']+", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(Authorization\s*:\s*Basic\s+)[A-Za-z0-9+/=]+", re.IGNORECASE),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\b(OPNSENSE_API_KEY|OPNSENSE_API_SECRET|DISCORD_WEBHOOK_URL)\s*=\s*[^\s\"']+", re.IGNORECASE),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"\b(OPNSENSE_API_KEY|OPNSENSE_API_SECRET|DISCORD_WEBHOOK_URL)\s*:\s*[^\s\"']+", re.IGNORECASE),
        r"\1: [REDACTED]",
    ),
]


def redact_sensitive_text(value):
    if value is None:
        return ""

    text = str(value)
    for pattern, replacement in _REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text
