#!/bin/bash
# update_install.sh - Simple script to update or install this project from its git repository


# Install prerequisites: curl, python3, default-jre-headless
echo "Installing prerequisites: curl, python3, default-jre-headless..."
apt update && apt upgrade -y
apt install -y curl python3 default-jre-headless git python3-pip python3-flask



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

echo "Update/Install complete."

# --- Minecraft server auto-update logic ---
cd "$SERVER_DIR" || exit 1

# Download version manifest
VERSION_MANIFEST_URL="https://launchermeta.mojang.com/mc/game/version_manifest.json"
VERSION_MANIFEST_JSON="$(curl -fsSL "$VERSION_MANIFEST_URL")"
LATEST_VERSION=$(echo "$VERSION_MANIFEST_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['latest']['release'])")

# Get current installed version (if any)
if [ -f server.jar.version ]; then
    CURRENT_VERSION=$(cat server.jar.version)
else
    CURRENT_VERSION="none"
fi

if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    echo "Updating Minecraft server to version $LATEST_VERSION..."
    # Get version metadata URL
    VERSION_URL=$(echo "$VERSION_MANIFEST_JSON" | python3 -c "import sys, json; v=json.load(sys.stdin); print([x['url'] for x in v['versions'] if x['id']=='$LATEST_VERSION'][0])")
    VERSION_JSON="$(curl -fsSL "$VERSION_URL")"
    SERVER_JAR_URL=$(echo "$VERSION_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['downloads']['server']['url'])")
    curl -fsSL -o server.jar "$SERVER_JAR_URL"
    if [ $? -eq 0 ]; then
        echo "$LATEST_VERSION" > server.jar.version
        echo "Minecraft server updated to $LATEST_VERSION."
    else
        echo "Failed to download server.jar."
    fi
else
    echo "Minecraft server is already up to date ($CURRENT_VERSION)."
fi

