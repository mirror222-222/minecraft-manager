
# Minecraft Manager

**TL;DR: Install/Run on target system**

Run this one-liner from your bash prompt (no need to download anything manually):

```sh
curl -fsSL https://raw.githubusercontent.com/mirror222-222/minecraft-manager/main/update_install.sh | sudo bash
```

This will install the Minecraft Manager into `/opt/minecraftmanager` and set up the Minecraft server in `/opt/minecraft`.

A development environment for managing Minecraft servers and scripts, using Python and Bash.

## Features
- Python scripting
- Bash utilities
- Dev container support for consistent development

## Getting Started
1. Open this folder in VS Code.
2. Reopen in Container when prompted (or use the Command Palette: "Dev Containers: Reopen in Container").
3. Start developing with Python and Bash!

## Requirements
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)


## Structure
- `.devcontainer/` - Dev container configuration
- `main.py` - Web manager entry point (project root)
- `hello.sh` - Example script (project root)
- `src/actions/` - Python scripts for server actions
- `src/static/` - Static files (CSS, JS)
- `src/templates/` - HTML templates
- `update_install.sh` - Installer/Updater script
- `README.md`, `LICENSE`, etc. (project root)

---


---

## Usage (Development)
1. Open this folder in VS Code.
2. Reopen in Container when prompted (or use the Command Palette: "Dev Containers: Reopen in Container").
3. Start developing with Python and Bash!

## Usage (Production/Target Install)
Run the TL;DR command above. All manager code will be in `/opt/minecraftmanager` and the Minecraft server in `/opt/minecraft`.
