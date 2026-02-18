#!/bin/bash
# update_install.sh - Simple script to update or install this project from its git repository


# Install prerequisites: curl, python3, default-jre-headless
echo "Installing prerequisites: curl, python3, default-jre-headless..."
apt update && apt upgrade -y
apt install -y curl python3 default-jre-headless git python3-pip python3-flask python3-mcstatus



REPO_URL="https://github.com/mirror222-222/minecraft-manager.git"
APP_DIR="/opt/minecraftmanager"
SERVER_DIR="/opt/minecraft"

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
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
fi


echo "Running application..."
if [ -f main.py ]; then
    python3 main.py
else
    echo "main.py not found."
fi


echo "Setting up Minecraft server as a systemd service..."
# Create minecraft user if not exists
if ! id minecraft &>/dev/null; then
    useradd -r -m -d "$SERVER_DIR" minecraft
fi

# Copy systemd unit file
cp "$APP_DIR/minecraft.service" /etc/systemd/system/minecraft.service
chown root:root /etc/systemd/system/minecraft.service
chmod 644 /etc/systemd/system/minecraft.service

# Ensure server files owned by minecraft user
chown -R minecraft:minecraft "$SERVER_DIR"

# Enable the service (do not start)
systemctl daemon-reload
systemctl enable minecraft

echo "Minecraft server systemd service setup complete."
    SERVER_JAR_URL=$(echo "$VERSION_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['downloads']['server']['url'])")

