#!/bin/bash
# update_install.sh - Simple script to update or install this project from its git repository


# Install prerequisites: curl, python3, python3-venv, default-jre-headless
echo "Installing prerequisites: curl, python3, python3-venv, default-jre-headless..."
apt update && apt upgrade -y
apt install -y curl python3 python3-venv default-jre-headless git



REPO_URL="https://github.com/mirror222-222/minecraft-manager.git"
APP_DIR="/opt/minecraftmanager"
SERVER_DIR="/opt/minecraft"
VENV_DIR="$APP_DIR/.venv"

# After cloning, move all project files (main.py, update_install.sh, README.md, etc.) to /opt/minecraftmanager root



# Install or update the app code in /opt/minecraftmanager
if [ ! -d "$APP_DIR" ]; then
    echo "Creating $APP_DIR..."
    mkdir -p "$APP_DIR"
fi


if [ -d "$APP_DIR/.git" ]; then
    echo "Updating existing repository in $APP_DIR..."
    cd "$APP_DIR" || { echo "Failed to cd to $APP_DIR"; exit 1; }
    git pull origin main || { echo "git pull failed"; exit 1; }
else
    if [ -d "$APP_DIR" ] && [ ! -d "$APP_DIR/.git" ]; then
        echo "$APP_DIR exists but is not a git repo. Removing..."
        rm -rf "$APP_DIR"
        mkdir -p "$APP_DIR"
    fi
    echo "Cloning repository into $APP_DIR..."
    git clone "$REPO_URL" "$APP_DIR" || { echo "git clone failed"; exit 1; }
    cd "$APP_DIR" || { echo "Failed to cd to $APP_DIR after clone"; exit 1; }
fi


# No need to move files; repo is now structured with main.py and hello.sh at the root.


echo "Installing Python dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR" || { echo "Failed to create virtual environment"; exit 1; }
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip || { echo "Failed to upgrade pip in venv"; exit 1; }

if [ -f requirements.txt ]; then
    "$VENV_DIR/bin/pip" install -r requirements.txt || { echo "Failed to install requirements in venv"; exit 1; }
fi


echo "Application install complete."


echo "Setting up Minecraft server as a systemd service..."
# Create minecraft user if not exists
if ! id minecraft &>/dev/null; then
    useradd -r -m -d "$SERVER_DIR" minecraft
fi

# Copy systemd unit file
cp "$APP_DIR/minecraft.service" /etc/systemd/system/minecraft.service
chown root:root /etc/systemd/system/minecraft.service
chmod 644 /etc/systemd/system/minecraft.service

# Copy web manager systemd unit file
cp "$APP_DIR/minecraft-manager.service" /etc/systemd/system/minecraft-manager.service
chown root:root /etc/systemd/system/minecraft-manager.service
chmod 644 /etc/systemd/system/minecraft-manager.service

# Copy idle monitor systemd unit file
cp "$APP_DIR/minecraft-idle-monitor.service" /etc/systemd/system/minecraft-idle-monitor.service
chown root:root /etc/systemd/system/minecraft-idle-monitor.service
chmod 644 /etc/systemd/system/minecraft-idle-monitor.service

# Ensure server files owned by minecraft user
chown -R minecraft:minecraft "$SERVER_DIR"

# Enable services (start web manager now)
systemctl daemon-reload
systemctl enable minecraft
systemctl enable --now minecraft-manager
systemctl enable --now minecraft-idle-monitor

echo "Minecraft server, web manager, and idle monitor systemd service setup complete."

