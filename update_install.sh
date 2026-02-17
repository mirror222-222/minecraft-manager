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
