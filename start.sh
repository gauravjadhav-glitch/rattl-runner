#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

# Trap Control+C to cleanup
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Ratl Runner..."

# Start Backend
echo "🐍 Starting Backend (Port 8000)..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo "⚛️ Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Both services reported running."
echo "Press Ctrl+C to stop."

# Wait for processes
wait
