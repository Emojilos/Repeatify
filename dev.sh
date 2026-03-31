#!/bin/bash
# Start backend and frontend in dev mode with hot-reload

ROOT="$(cd "$(dirname "$0")" && pwd)"

trap 'kill 0' EXIT

echo "Starting backend (http://localhost:8000)..."
cd "$ROOT/backend" && env $(grep -v '^#' "$ROOT/.env" | xargs) uvicorn app.main:app --reload --port 8000 &

echo "Starting frontend (http://localhost:5173)..."
cd "$ROOT/frontend" && VITE_API_URL=http://localhost:8000 npm run dev &

wait
