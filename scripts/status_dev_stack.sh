#!/usr/bin/env bash
set -euo pipefail

TMP_DIR="${TMPDIR:-/tmp}"
FRONTEND_PID_FILE="$TMP_DIR/football-frontend.pid"
BACKEND_PID_FILE="$TMP_DIR/football-backend.pid"

print_status() {
  local name="$1"
  local pid_file="$2"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$name running: $(cat "$pid_file")"
  else
    echo "$name stopped"
  fi
}

print_status "frontend" "$FRONTEND_PID_FILE"
print_status "backend" "$BACKEND_PID_FILE"
