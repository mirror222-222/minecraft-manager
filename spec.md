# Minecraft Manager Project Specification

## Overview
A simple web-based manager for a Minecraft Java server, providing controls to start/stop the server and edit the whitelist. The manager will be accessible via a webpage with the following features:


## Features

### Webpage UI
- **Start Minecraft** button
- **Stop Minecraft** button
- **Edit Whitelist** text area (for editing `whitelist.json`)
- **Submit** button to update the whitelist and reboot the server
- **Status/Notice** area for displaying success or error messages

### Backend Logic
- **Stop Button**
  - Stops the Minecraft server service
  - On completion, displays "Server stopped" or an error message

- **Start Button**
  - Runs `apt update`
  - Checks for the latest Minecraft Java server version
    - If not present or outdated, downloads the latest version
  - Ensures `eula.txt` exists and contains `eula=true`
  - Ensures the server is in allowlist-only mode (users must be in `whitelist.json` to join)
  - Starts the Minecraft server service
  - On completion, displays "Server started" or an error message

- **Edit Whitelist**
  - Allows editing of the `whitelist.json` file via the webpage
  - On submit, updates the file and restarts the Minecraft server service

- **Automatic Idle Shutdown**
  - Once the Minecraft server is running, the backend will check every minute to see how many users are connected.
  - If there are no users connected for 30 consecutive minutes, the server will be automatically stopped.
  - A notice will be displayed in the web UI when the server is stopped due to inactivity.

## Technical Requirements
- **Frontend:** Simple HTML/CSS/JavaScript (can use Flask/Jinja2 for templating)
- **Backend:** Python (Flask web server)
- **System Integration:**
  - Use subprocess or systemd to control the Minecraft server service
  - Use Python to read/write `whitelist.json` and manage `eula.txt`
  - Use Python to run `apt update` and download server jar as needed

## File Structure
- `src/`
  - `main.py` (Flask app and backend logic)
  - `templates/` (HTML templates)
  - `static/` (CSS/JS)
- `README.md` (project documentation)
- `whitelist.json` (Minecraft server whitelist)
- `eula.txt` (Minecraft server EULA)

## Future Enhancements (Optional)
- Authentication for the web manager
- Server log viewer
- Backup/restore functionality

---
This spec provides a clear roadmap for implementing the Minecraft Manager as described.