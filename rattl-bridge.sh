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

OS_TYPE=$(uname)
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

# Integrity Check: Remove if invalid
if [ -f "$CLOUDFLARED_BIN" ]; then
    if ! "$CLOUDFLARED_BIN" --version &> /dev/null; then
        echo "⚠️  Corrupt Cloudflared binary detected. Re-downloading..."
        rm "$CLOUDFLARED_BIN"
    fi
fi

if [ ! -f "$CLOUDFLARED_BIN" ]; then
    echo "⬇️  Cloudflared not found. Downloading standalone binary..."
    
    URL=""
    IS_TGZ=false
    
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        IS_TGZ=true
        if [[ "$ARCH_TYPE" == "arm64" ]]; then
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
        else
            URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
        fi
    else
        # Linux usually provides a direct binary
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    fi
    
    # Use -f to fail on 404 errors, -L to follow redirects
    if [ "$IS_TGZ" = true ]; then
        if curl -fL -o "$BIN_DIR/cloudflared.tgz" "$URL"; then
             tar -xzf "$BIN_DIR/cloudflared.tgz" -C "$BIN_DIR"
             rm "$BIN_DIR/cloudflared.tgz"
             chmod +x "$CLOUDFLARED_BIN"
             echo "✅ Cloudflared installed locally."
        else
             echo "❌ Critical Error: Failed to download Cloudflared archive."
             echo "   URL: $URL"
             exit 1
        fi
    else
        if curl -fL -o "$CLOUDFLARED_BIN" "$URL"; then
            chmod +x "$CLOUDFLARED_BIN"
            echo "✅ Cloudflared installed locally."
        else
            echo "❌ Critical Error: Failed to download Cloudflared binary."
            echo "   URL: $URL"
            rm -f "$CLOUDFLARED_BIN"
            exit 1
        fi
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

# Attempt to install dependencies
echo "📦 Installing dependencies..."
if ! ./venv/bin/pip install -r requirements.txt; then
    echo "⚠️  Dependency install failed. Possible broken environment."
    echo "♻️  Recreating Python virtual environment..."
    rm -rf venv
    python3 -m venv venv
    
    # Retry install
    if ! ./venv/bin/pip install -r requirements.txt; then
        echo "❌ Critical Error: Failed to install Python dependencies."
        exit 1
    fi
fi

# --- 5. Execution ---

# Kill old processes
echo "🧹 Clearing old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start Backend
echo "🐍 Starting Backend..."
# Use unbuffered output for Python to see logs immediately
export PYTHONUNBUFFERED=1
# Use venv python explicitly
./venv/bin/python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to initialize..."
MAX_RETRIES=10
RETRIES=0
BACKEND_READY=false

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if lsof -i:8000 -t >/dev/null 2>&1 || curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1; then
        BACKEND_READY=true
        break
    fi
    # Check if process died
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died unexpectedly!"
        break
    fi
    sleep 1
    RETRIES=$((RETRIES+1))
done

if [ "$BACKEND_READY" = false ]; then
    echo "❌ Error: Backend failed to start on port 8000."
    echo "--- 📜 ID: backend.log (Last 20 lines) ---"
    tail -n 20 backend/backend.log
    echo "------------------------------------------"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start Tunnel
echo "--------------------------------------------------------"
echo "✨ BRIDGE READY"
echo "--------------------------------------------------------"
echo "👉 STEPS:"
echo "1. Wait for the 'https://' link below."
echo "2. Copy it."
echo "3. Go to https://rattl-runner.vercel.app/"
echo "4. Click 'NOT DETECTED' -> Paste Link -> Connect."
echo "--------------------------------------------------------"

# Use explicit 127.0.0.1 to avoid IPv6 ::1 connection refused errors
"$CLOUDFLARED_BIN" tunnel --url http://127.0.0.1:8000

# Cleanup
trap "kill $BACKEND_PID; exit" INT
wait
