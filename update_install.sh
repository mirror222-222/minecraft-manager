#!/bin/bash
# update_install.sh - Simple script to update or install this project from its git repository

REPO_URL="https://github.com/mirror222-222/minecraft-manager.git"

TARGET_DIR="/opt/minecraft"
TARGET_DIR="/opt/minecraft"


if [ -d "$TARGET_DIR/.git" ]; then
    echo "Updating existing repository in $TARGET_DIR..."
    cd "$TARGET_DIR" || exit 1
    git pull origin main
else
    echo "Cloning repository into $TARGET_DIR..."
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR" || exit 1
fi

echo "Installing Python dependencies..."

if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
fi

echo "Running application..."

if [ -f src/main.py ]; then
    python3 src/main.py
else
    echo "src/main.py not found."
fi

echo "Update/Install complete."
# --- Minecraft server auto-update logic ---
cd "$TARGET_DIR" || exit 1

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

