#!/usr/bin/env bash
set -e

# 1. Start Backend
echo "Starting backend on http://localhost:8000 ..."
# Use the python.exe inside your backend venv directly
./backend/venv/Scripts/python.exe -m uvicorn api_server:app --reload --port 8000 --app-dir backend &
BACK_PID=$!

# Give backend a moment to boot
sleep 2

# 2. Start Frontend
echo "Starting frontend on http://localhost:5173 ..."
# Move into frontend, run it, then move back
cd frontend
npm run dev
cd ..

# When frontend exits, stop backend too
kill $BACK_PID >/dev/null 2>&1 || true