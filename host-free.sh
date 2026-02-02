#!/bin/bash

# This script helps you host your project for free

echo "--- Ratl Runner Cloud Hosting Setup ---"

# 1. Start Backend with Docker
echo "Building and starting Backend container..."
cd backend
docker build -t ratl-backend .
docker run -d -p 8000:8000 --name ratl-backend --privileged -v /dev/bus/usb:/dev/bus/usb ratl-backend

# 2. Start Tunnel (using Pinggy for zero-setup)
echo "------------------------------------------------"
echo "Starting public tunnel for your backend..."
echo "COPY THE URL BELOW AND USE IT AS VITE_API_URL"
echo "------------------------------------------------"
ssh -R 80:localhost:8000 pgy.in
