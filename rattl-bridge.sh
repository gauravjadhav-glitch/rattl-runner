#!/bin/bash

# --- Rattl Studio Ultimate Bridge (Portable) ---
# Zero-dependency version: Downloads binaries locally. No Homebrew/Node/Sudo required.

echo "🚀 Initializing Rattl Studio Bridge (Portable)..."

# --- 1. Environment Setup ---
WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
BIN_DIR="$WORKDIR/.bin"
mkdir -p "$BIN_DIR"
export PATH="$BIN_DIR:$PATH"
export PATH="$BIN_DIR/platform-tools:$PATH"

OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

echo "ℹ️  System: $OS_TYPE ($ARCH_TYPE)"

# --- 2. Check/Download ADB ---
if ! command -v adb &> /dev/null; then
    echo "⬇️  ADB not found. Downloading standalone version..."
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        curl -sL -o "$BIN_DIR/platform-tools.zip" "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
    else
        curl -sL -o "$BIN_DIR/platform-tools.zip" "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
    fi
    
    # Unzip quietly
    unzip -q "$BIN_DIR/platform-tools.zip" -d "$BIN_DIR"
    rm "$BIN_DIR/platform-tools.zip"
    
    if [ -f "$BIN_DIR/platform-tools/adb" ]; then
        echo "✅ ADB installed locally."
    else
        echo "❌ Failed to install ADB. Please install manually."
        exit 1
    fi
else
    echo "✅ ADB detected."
fi

# --- 3. Check/Download Cloudflared (Tunnel) ---
CLOUDFLARED_BIN="$BIN_DIR/cloudflared"
if [ ! -f "$CLOUDFLARED_BIN" ]; then
    echo "⬇️  Cloudflared not found. Downloading standalone binary..."
    
    URL=""
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        if [[ "$ARCH_TYPE" == "arm64" ]]; then
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64"
        else
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64"
        fi
    else
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    fi
    
    curl -sL -o "$CLOUDFLARED_BIN" "$URL"
    chmod +x "$CLOUDFLARED_BIN"
    
    if [ -f "$CLOUDFLARED_BIN" ]; then
        echo "✅ Cloudflared installed locally."
    else
        echo "❌ Failed to download Cloudflared."
        exit 1
    fi
else
    echo "✅ Cloudflared detected."
fi

# --- 4. Setup Python Environment ---
echo "� Setting up Python environment..."
cd "$WORKDIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# --- 5. Execution ---

# Kill old processes
echo "🧹 Clearing old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start Backend
echo "� Starting Backend..."
python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 2

# Start Tunnel
echo "--------------------------------------------------------"
echo "✨ BRIDGE READY"
echo "--------------------------------------------------------"
echo "👉 STEPS:"
echo "1. Wait for the 'https://' link below."
echo "2. Copy it."
echo "3. Go to https://rattl-runner.vercel.app/"
echo "4. Click 'NOT DETECTED' -> Paste Link -> Update."
echo "--------------------------------------------------------"

"$CLOUDFLARED_BIN" tunnel --url http://localhost:8000

# Cleanup
trap "kill $BACKEND_PID; exit" INT
wait
