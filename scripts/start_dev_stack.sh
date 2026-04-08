#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${TMPDIR:-/tmp}"

FRONTEND_PID_FILE="$TMP_DIR/football-frontend.pid"
FRONTEND_LOG_FILE="$TMP_DIR/football-frontend.log"
BACKEND_PID_FILE="$TMP_DIR/football-backend.pid"
BACKEND_LOG_FILE="$TMP_DIR/football-backend.log"

start_frontend() {
  if [[ -f "$FRONTEND_PID_FILE" ]] && kill -0 "$(cat "$FRONTEND_PID_FILE")" 2>/dev/null; then
    echo "frontend already running: $(cat "$FRONTEND_PID_FILE")"
    return
  fi

  rm -f "$FRONTEND_PID_FILE"
  rm -rf "$ROOT_DIR/frontend/.next"

  (
    cd "$ROOT_DIR/frontend"
    nohup npm run dev -- --hostname 127.0.0.1 --port 3000 >"$FRONTEND_LOG_FILE" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )

  echo "frontend started: $(cat "$FRONTEND_PID_FILE")"
}

start_backend() {
  if [[ -f "$BACKEND_PID_FILE" ]] && kill -0 "$(cat "$BACKEND_PID_FILE")" 2>/dev/null; then
    echo "backend already running: $(cat "$BACKEND_PID_FILE")"
    return
  fi

  rm -f "$BACKEND_PID_FILE"

  (
    cd "$ROOT_DIR"
    nohup ./.venv/bin/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000 >"$BACKEND_LOG_FILE" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )

  echo "backend started: $(cat "$BACKEND_PID_FILE")"
}

start_backend
start_frontend

echo "logs:"
echo "  backend  $BACKEND_LOG_FILE"
echo "  frontend $FRONTEND_LOG_FILE"
