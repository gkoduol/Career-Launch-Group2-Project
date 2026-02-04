#!/usr/bin/env bash
set -e

# Define a cleanup function
cleanup() {
    echo "Stopping backend..."
    kill $BACK_PID
    exit
}

# TRAP: If the script is interrupted (SIGINT/Ctrl+C) or exits, run 'cleanup'
trap cleanup SIGINT EXIT

# 1. Start Backend
echo "Starting backend on http://localhost:8000 ..."
./backend/venv/Scripts/python.exe -m uvicorn api_server:app --reload --port 8000 --app-dir backend &
BACK_PID=$!

# Give backend a moment to boot
sleep 2

# 2. Start Frontend
echo "Starting frontend on http://localhost:5173 ..."
cd frontend
npm run dev