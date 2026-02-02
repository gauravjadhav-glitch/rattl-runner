#!/bin/bash

# --- Rattl Studio Ultimate Bridge ---
# This script automates ADB, the Backend, and the Secure Tunnel.

echo "🚀 Starting Rattl Studio Bridge..."

# 1. Check for ADB
if ! command -v adb &> /dev/null
then
    echo "❌ ADB not found. Please install Android Platform Tools."
    exit 1
fi

# 2. Check for Node (needed for localtunnel)
if ! command -v lt &> /dev/null
then
    echo "📦 Installing Localtunnel helper..."
    npm install -g localtunnel
fi

# 3. Kill any existing backend on port 8000
echo "🧹 Clearing old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 4. Start Backend in background
echo "🐍 Starting Backend..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1
python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to wake up
sleep 2

# 5. Start Tunnel
echo "🌐 Creating Secure Bridge to Vercel..."
# Generate a unique subdomain based on username to avoid conflicts
USER_HASH=$(echo $USER | md5 | cut -c1-6)
SUBDOMAIN="rattl-$USER_HASH"

echo "--------------------------------------------------------"
echo "✨ BRIDGE ACTIVE!"
echo "--------------------------------------------------------"
echo "👉 COPY THIS URL:"
lt --port 8000 --subdomain $SUBDOMAIN | grep -o "https://.*" 
echo "--------------------------------------------------------"
echo "1. Open https://rattl-runner.vercel.app/"
echo "2. Click 'NOT DETECTED' at the top."
echo "3. Paste the URL above."
echo "--------------------------------------------------------"
echo "Press Ctrl+C to stop the bridge."

# Keep it running
trap "kill $BACKEND_PID; exit" INT
wait
