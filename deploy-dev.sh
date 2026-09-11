#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/var/devprof/enroll
APP_HOST=127.0.0.1
APP_PORT=8008
VENV_PYTHON="$APP_DIR/venv/bin/python"
LOG_FILE="$APP_DIR/dev.out"
LOCK_DIR=/tmp/enroll-dev-deploy.lock

[[ "$APP_DIR" == /var/devprof/enroll ]]
[[ "$APP_PORT" == 8008 ]]
cd "$APP_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "A dev deployment is already running" >&2
    exit 1
fi
trap 'rmdir "$LOCK_DIR"' EXIT

test -x "$VENV_PYTHON"
test -f .env
set -a
source .env
set +a
git fetch --prune origin main
git diff --quiet
git diff --cached --quiet
git reset --hard origin/main
"$VENV_PYTHON" -m py_compile run_dev.py

listener_pid=$(ss -ltnp 2>/dev/null | awk -v endpoint="$APP_HOST:$APP_PORT" '$0 ~ endpoint && match($0, /pid=[0-9]+/) { print substr($0, RSTART + 4, RLENGTH - 4); exit }')
if [[ -n "$listener_pid" ]]; then
    kill "$listener_pid"
    for _ in {1..20}; do
        if ! kill -0 "$listener_pid" 2>/dev/null; then
            break
        fi
        sleep 0.25
    done
    if kill -0 "$listener_pid" 2>/dev/null; then
        echo "Dev listener PID $listener_pid did not stop" >&2
        exit 1
    fi
fi

nohup "$VENV_PYTHON" run_dev.py >> "$LOG_FILE" 2>&1 < /dev/null &
echo "Started dev app PID $! on $APP_HOST:$APP_PORT"
