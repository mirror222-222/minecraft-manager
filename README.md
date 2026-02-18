# Minecraft Manager

Web-based manager for a Minecraft Java server with systemd integration.

## Quick Install (Target Host)

```sh
curl -fsSL https://raw.githubusercontent.com/mirror222-222/minecraft-manager/main/update_install.sh | sudo bash
```

This installs:
- App code in `/opt/minecraftmanager`
- Minecraft server files in `/opt/minecraft`
- Python virtual environment in `/opt/minecraftmanager/.venv`

## What It Does

- Start/stop Minecraft server from a web UI
- Edit and apply `whitelist.json` from the web UI
- Auto-stop server after 30 minutes with 0 connected players
- Show inactivity shutdown notice in the web UI

## Services

The installer configures these systemd services:

- `minecraft.service` (Minecraft Java server)
	- Enabled at boot
	- Not auto-started during install
- `minecraft-manager.service` (Flask web UI)
	- Enabled and started immediately during install (`enable --now`)
- `minecraft-idle-monitor.service` (inactivity monitor)
	- Enabled and started immediately during install (`enable --now`)

## Service Commands

```sh
sudo systemctl status minecraft
sudo systemctl status minecraft-manager
sudo systemctl status minecraft-idle-monitor

sudo systemctl restart minecraft-manager
sudo systemctl restart minecraft-idle-monitor
```

## Troubleshooting

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

## Project Layout

- `main.py` - Flask web app
- `actions/` - Action scripts (`start_server.py`, `stop_server.py`, `update_whitelist.py`, `idle_monitor.py`)
- `templates/` - Jinja templates
- `static/` - Static assets
- `minecraft.service` - Minecraft systemd unit
- `minecraft-manager.service` - Web UI systemd unit
- `minecraft-idle-monitor.service` - Idle monitor systemd unit
- `update_install.sh` - Install/update script

## Development

Run locally from repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
