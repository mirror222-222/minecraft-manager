# Minecraft Manager

Web-based manager for a Minecraft Java server with systemd integration.

## 1) Purpose

Minecraft Manager provides a web UI and automation for operating a Minecraft Java server on Linux.

## 2) Quick Install (Target Host)

```sh
curl -fsSL https://raw.githubusercontent.com/mirror222-222/minecraft-manager/main/update_install.sh | sudo bash
```

Then update:
- `/etc/minecraft-manager/opnsense.env`

This installs:
- App code in `/opt/minecraftmanager`
- Minecraft server files in `/opt/minecraft`
- Python virtual environment in `/opt/minecraftmanager/.venv`

## 3) Runtime Layout

- Application directory: `/opt/minecraftmanager`
- Server directory: `/opt/minecraft`
- Python environment: `/opt/minecraftmanager/.venv`

## 4) Implemented Features

- Start/stop Minecraft server from a web UI
- Manual "Allow External Access" action that enables a configured OPNsense firewall rule only after Minecraft is reachable
- External access status indicator in the web UI (enabled / disabled / unavailable)
- Edit and apply `whitelist.json` from the web UI
- Auto-stop server after 30 minutes with 0 connected players
- Show inactivity shutdown notice in the web UI
- Always disable the configured OPNsense firewall rule when server stop is triggered (manual stop and idle auto-stop)

## 5) System Services

The installer configures these systemd services:

- `minecraft.service` (Minecraft Java server)
  - Enabled at boot
  - Not auto-started during install
- `minecraft-manager.service` (Flask web UI)
  - Enabled and started immediately during install (`enable --now`)
- `minecraft-idle-monitor.service` (inactivity monitor)
  - Enabled and started immediately during install (`enable --now`)

## 6) Operations

Service status:

```sh
sudo systemctl status minecraft
sudo systemctl status minecraft-manager
sudo systemctl status minecraft-idle-monitor
```

Restart control services:

```sh
sudo systemctl restart minecraft-manager
sudo systemctl restart minecraft-idle-monitor
```

## 6.1) OPNsense Firewall API Secrets

Firewall credentials are loaded from a root-only systemd environment file:

- `/etc/minecraft-manager/opnsense.env`

Required variables:

```sh
OPNSENSE_URL="https://your-opnsense-host"
OPNSENSE_API_KEY="your_api_key"
OPNSENSE_API_SECRET="your_api_secret"
OPNSENSE_RULE_UUID="your_rule_uuid"
```

Optional variable:

```sh
OPNSENSE_VERIFY_TLS="0"
```

- Default is `0` (TLS verification disabled, equivalent to `curl -k` behavior).
- Set to `1` to require valid TLS certificates.

After editing the env file:

```sh
sudo systemctl daemon-reload
sudo systemctl restart minecraft-manager
sudo systemctl restart minecraft-idle-monitor
```

Workflow:

1. Start Minecraft.
2. Wait for server readiness.
3. Click **Allow External Access** in the web UI.
4. When server is stopped (manual or idle timeout), firewall rule is disabled automatically.

## 7) Troubleshooting

Check service health:

```sh
sudo systemctl status minecraft
sudo systemctl status minecraft-manager
sudo systemctl status minecraft-idle-monitor
```

View recent logs (newest first):

```sh
sudo journalctl -u minecraft -n 100 --no-pager -r
sudo journalctl -u minecraft-manager -n 100 --no-pager -r
sudo journalctl -u minecraft-idle-monitor -n 100 --no-pager -r
```

Follow logs live:

```sh
sudo journalctl -u minecraft -f
sudo journalctl -u minecraft-manager -f
sudo journalctl -u minecraft-idle-monitor -f
```

If a service does not start:

```sh
sudo systemctl daemon-reload
sudo systemctl restart minecraft-manager
sudo systemctl restart minecraft-idle-monitor
```

## 8) Project Layout

- `main.py` - Flask web app
- `actions/` - Action scripts (`start_server.py`, `stop_server.py`, `update_whitelist.py`, `idle_monitor.py`)
- `templates/` - Jinja templates
- `static/` - Static assets
- `minecraft.service` - Minecraft systemd unit
- `minecraft-manager.service` - Web UI systemd unit
- `minecraft-idle-monitor.service` - Idle monitor systemd unit
- `update_install.sh` - Install/update script

## 9) Development

Run locally from repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
