#!/bin/bash

# --- Rattl Studio Installer & Bridge ---
# This script sets up the Rattl Bridge on your local machine.
# It clones the repository if needed and starts the bridge connection.

echo "🚀 Initializing Rattl Studio Bridge..."

# Define the installation directory
INSTALL_DIR="rattl-runner"
REPO_URL="https://github.com/gauravjadhav-glitch/Rattl-runner.git"

# Check if we are already inside the project (e.g., user manually downloaded)
if [ -f "rattl-bridge.sh" ]; then
    echo "✅ Project files found in current directory."
    chmod +x rattl-bridge.sh
    ./rattl-bridge.sh
    exit 0
fi

# Check if the installation folder exists
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Found existing installation in ./$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    echo "🔄 Updating..."
    if [ -d ".git" ]; then
        git pull origin main || git pull origin master || echo "⚠️ Could not update via git. Continuing..."
    fi
else
    echo "⬇️ Downloading Rattl Runner..."
    # Check for git
    if ! command -v git &> /dev/null; then
        echo "❌ Error: 'git' is not installed. Please install git to continue."
        exit 1
    fi

    # Clone the repo
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Ensure executable permissions
chmod +x rattl-bridge.sh

# Run the bridge
./rattl-bridge.sh
