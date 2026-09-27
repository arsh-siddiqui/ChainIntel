#!/usr/bin/env bash
# ChainIntel local development launcher (macOS / Linux)
set -e
cd "$(dirname "$0")/.."

echo "ChainIntel dev launcher"

# 1. Backend
(cd backend
  [ -f .env ] || cp .env.example .env
  uvicorn app.main:app --reload --port 8000 &
  BACK_PID=$!
)

# 2. Frontend
(cd frontend
  [ -f .env.local ] || cp .env.local.example .env.local
  npm install --no-audit --no-fund
  npm run dev &
  FRONT_PID=$!
)

echo
echo "Backend:  http://localhost:8000  (docs at /docs)"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both."
trap "kill $BACK_PID $FRONT_PID 2>/dev/null" EXIT
wait
