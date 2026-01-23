#!/usr/bin/env bash
set -e

# If backend already running, don't crash the whole script
echo "Starting backend on http://localhost:8000 ..."
python3 -m uvicorn api_server:app --reload --port 8000 >/dev/null 2>&1 &
BACK_PID=$!

# Give backend a moment to boot
sleep 1

echo "Starting frontend on http://localhost:5173 ..."
npm run dev

# When frontend exits, stop backend too
kill $BACK_PID >/dev/null 2>&1 || true
