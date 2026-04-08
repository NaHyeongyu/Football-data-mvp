#!/usr/bin/env bash
set -euo pipefail

TMP_DIR="${TMPDIR:-/tmp}"
FRONTEND_PID_FILE="$TMP_DIR/football-frontend.pid"
BACKEND_PID_FILE="$TMP_DIR/football-backend.pid"

stop_process() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    echo "$name stopped: $pid"
  else
    echo "$name stale pid removed: $pid"
  fi

  rm -f "$pid_file"
}

stop_process "frontend" "$FRONTEND_PID_FILE"
stop_process "backend" "$BACKEND_PID_FILE"
