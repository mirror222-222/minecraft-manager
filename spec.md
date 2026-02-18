# Minecraft Manager Specification (Current Implementation)

## 1) Purpose

Minecraft Manager provides a web UI and automation for operating a Minecraft Java server on a Linux host using systemd.

This document describes the **current implemented design** only.

## 2) Runtime Layout

- Application directory: `/opt/minecraftmanager`
- Minecraft server directory: `/opt/minecraft`
- Python virtual environment: `/opt/minecraftmanager/.venv`

## 3) System Services

### 3.1 minecraft.service

- Runs the Minecraft Java server from `/opt/minecraft`.
- Enabled at boot by installer.
- Not auto-started during install.

### 3.2 minecraft-manager.service

- Runs Flask web UI using `/opt/minecraftmanager/.venv/bin/python /opt/minecraftmanager/main.py`.
- Enabled and started during install (`systemctl enable --now minecraft-manager`).

### 3.3 minecraft-idle-monitor.service

- Runs idle monitor using `/opt/minecraftmanager/.venv/bin/python /opt/minecraftmanager/actions/idle_monitor.py`.
- Enabled and started during install (`systemctl enable --now minecraft-idle-monitor`).

## 4) Web UI Behavior

### 4.1 Home Page

- Shows server status and user count when running.
- Shows start/stop controls (contextual by current server state).
- Shows editable whitelist JSON text area.
- Shows error log buffer (last 100 entries) with clear action.

### 4.2 Routes

- `GET /` renders dashboard.
- `POST /start` starts server workflow.
- `POST /stop` stops Minecraft service.
- `POST /whitelist` updates whitelist JSON and restarts server.
- `POST /errors/clear` clears in-memory app error log.
- `GET /status` returns JSON status (`running`, `users`).

## 5) Server Control Workflows

### 5.1 Start Workflow (`actions/start_server.py`)

- Ensures `/opt/minecraft` exists.
- Checks Mojang version manifest.
- Downloads/updates `server.jar` when missing or outdated.
- Writes `eula=true` to `eula.txt`.
- Ensures `enforce-whitelist=true` in `server.properties`.
- Starts `minecraft` service via systemd.
- Clears idle-shutdown notice file if present.

### 5.2 Stop Workflow (`actions/stop_server.py`)

- Stops `minecraft` service via systemd.
- Clears idle-shutdown notice file if present.

### 5.3 Whitelist Workflow (`actions/update_whitelist.py`)

- Overwrites `/opt/minecraft/whitelist.json` with submitted JSON.
- Stops and restarts `minecraft` service.
- Clears idle-shutdown notice file if present.

## 6) Idle Shutdown Design

Implemented by `actions/idle_monitor.py` and `minecraft-idle-monitor.service`.

- Poll interval: 60 seconds.
- Idle threshold: 30 consecutive minutes with zero online users.
- Player count source: `mcstatus` query to server host/port (derived from `server.properties`, defaults to `127.0.0.1:25565`).
- If threshold reached:
  - Stops `minecraft` service.
  - Writes inactivity notice file: `/opt/minecraft/idle_shutdown_notice.json`.

Web app reads this notice and displays a status message indicating server stopped due to inactivity.

## 7) File/Module Map (Current)

- `main.py`: Flask app and request handlers
- `actions/start_server.py`: startup/update logic
- `actions/stop_server.py`: stop logic
- `actions/update_whitelist.py`: whitelist + restart logic
- `actions/idle_monitor.py`: idle detection + auto-stop
- `minecraft.service`: Minecraft systemd unit
- `minecraft-manager.service`: web UI systemd unit
- `minecraft-idle-monitor.service`: idle monitor systemd unit
- `update_install.sh`: installer/updater and systemd setup
- `templates/index.html`, `static/style.css`: UI

## 8) Out of Scope (Current Build)

- Authentication/authorization
- Multi-server management
- Built-in backup scheduler
- In-app live log streaming UI