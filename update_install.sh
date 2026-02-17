#!/bin/bash
# update_install.sh - Simple script to update or install this project from its git repository

REPO_URL="https://github.com/mirror222-222/minecraft-manager.git"

# For private repos, set GITHUB_TOKEN or use username/password
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN not set. If this is a private repo, you can use your GitHub username and password (or personal access token as password)."
    read -p "GitHub Username: " GITHUB_USER
    read -s -p "GitHub Password or Token: " GITHUB_PASS
    echo
fi
TARGET_DIR="/opt/minecraft"


if [ -d "$TARGET_DIR/.git" ]; then
    echo "Updating existing repository in $TARGET_DIR..."
    cd "$TARGET_DIR" || exit 1
    if [ -n "$GITHUB_TOKEN" ]; then
        git pull "https://$GITHUB_TOKEN@${REPO_URL#https://}"
    elif [ -n "$GITHUB_USER" ] && [ -n "$GITHUB_PASS" ]; then
        git pull "https://$GITHUB_USER:$GITHUB_PASS@${REPO_URL#https://}"
    else
        git pull origin main
    fi
else
    echo "Cloning repository into $TARGET_DIR..."
    if [ -n "$GITHUB_TOKEN" ]; then
        git clone "https://$GITHUB_TOKEN@${REPO_URL#https://}" "$TARGET_DIR"
    elif [ -n "$GITHUB_USER" ] && [ -n "$GITHUB_PASS" ]; then
        git clone "https://$GITHUB_USER:$GITHUB_PASS@${REPO_URL#https://}" "$TARGET_DIR"
    else
        git clone "$REPO_URL" "$TARGET_DIR"
    fi
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
