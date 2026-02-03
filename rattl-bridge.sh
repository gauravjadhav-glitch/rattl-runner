#!/bin/bash

# --- Rattl Studio Ultimate Bridge (V2) ---
# This version uses Cloudflare Tunnels (npx cloudflared) which 
# is highly resistant to firewalls and "Connection Refused" errors.

echo "🚀 Starting Rattl Studio Bridge..."

# 1. Dependency Check & Auto-Install
check_install() {
    CMD=$1
    PKG=$2
    NAME=$3
    
    if ! command -v $CMD &> /dev/null; then
        echo "⚠️  $NAME not found."
        if [[ "$OSTYPE" == "darwin"* ]]; then
             echo "🍏 MacOS detected. Checking for Homebrew..."
             if ! command -v brew &> /dev/null; then
                 echo "❌ Homebrew not found. Installing Homebrew..."
                 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                 
                 # Add brew to path for this session if it was just installed
                 eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
             fi
             
             echo "📦 Installing $NAME..."
             brew install $PKG
        else
             echo "❌ Automatic install failed. Please install $NAME manually."
             exit 1
        fi
    fi
}

# Check for ADB
check_install "adb" "android-platform-tools" "Android Platform Tools"

# Check for Node/NPX (Required for Cloudflare Tunnel)
check_install "npx" "node" "Node.js"

# 2. Kill any existing backend on port 8000
echo "🧹 Clearing old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 3. Start Backend in background
echo "🐍 Starting Backend on Port 8000..."
cd backend
# Ensure requirements are installed
pip install -r requirements.txt > /dev/null 2>&1
# Start the backend
python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to wake up
sleep 2

# 4. Start Tunnel using Cloudflare (No-install, Firewall-friendly)
echo "🌐 Creating Secure Bridge via Cloudflare..."
echo "--------------------------------------------------------"
echo "✨ BRIDGE INITIALIZING..."
echo "--------------------------------------------------------"
echo "👉 STEPS:"
echo "1. Wait for Cloudflare to give you an 'https://' link below."
echo "2. Copy that link."
echo "3. Open https://rattl-runner.vercel.app/"
echo "4. Click 'NOT DETECTED' at the top and paste the link."
echo "--------------------------------------------------------"

# Run cloudflared tunnel
# It will output the URL to the terminal
npx cloudflared tunnel --url http://localhost:8000

# Cleanup on exit
trap "kill $BACKEND_PID; exit" INT
wait
